import csv
import logging
import time
from datetime import timedelta
from decimal import Decimal

from cryptocompy import price
from forex_python.converter import CurrencyRates, RatesNotAvailableError

from src.DateUtils import parse_date, date_to_string, get_start_of_year, get_start_of_year_after
from src.NumberUtils import value_to_decimal
from src.bo.ExchangeRate import ExchangeRate
from src.bo.ExchangeRateSource import ExchangeRateSource


class ExchangeRateImportError(Exception):
    """
    Signals an error while importing exchange rates.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)


def is_fiat(currency):
    """
    Returns true if the specified currency is a fiat currency.
    """
    return currency == 'EUR' or currency == 'USD'


def is_crypto(currency):
    """
    Returns true if the specified currency is a crypto currency.
    """
    return not is_fiat(currency)


class ExchangeRates:

    def __init__(self, configuration):
        self._query_apis = configuration.get_mandatory('query-exchange-rate-apis')
        self._tax_year = configuration.get_mandatory('tax-year')
        self._date_from = get_start_of_year(self._tax_year)
        self._date_to = get_start_of_year_after(self._tax_year)
        self._exchange_rates = {}
        self._cryptocompare_already_queried = []

        self._sources = {
            'cryptocompare': ExchangeRateSource('cryptocompare', 'cryptocompare.com',
                                                'crypto currency exchange rate queried from '
                                                'https://min-api.cryptocompare.com/'),
            'ratesapi': ExchangeRateSource('ratesapi', 'ratesapi.io',
                                           'fiat exchange rate queried from https://ratesapi.io/api/'),
            'implicit': ExchangeRateSource('implicit', '(implicit)', 'implicit exchange rate')
        }

        self.load_exchange_rates_from_configured_files(configuration)

    def get_exchange_rate(self, base_currency, quote_currency, timestamp):
        """
        Searches the available exchange rate data for an entry that matches the currency pair and is as close
        as possible to the specified timestamp.
        :returns: an exchange entry or None if no entry was found
        """

        exchange_rate = None

        if base_currency == quote_currency:  # same currency: get implicit exchange rate of 1
            return self.get_implicit_exchange_rate(base_currency, quote_currency, Decimal('1'), timestamp)

        if self._exchange_rates is not None:
            exchange_rate = self._get_exchange_rate_from_memory(base_currency, quote_currency, timestamp)

        if exchange_rate is not None:
            return exchange_rate

        if not self._query_apis:
            return None

        if is_crypto(base_currency) or is_crypto(quote_currency):

            self._query_exchange_rates_from_cryptocompare(base_currency, quote_currency)
            return self._get_exchange_rate_from_memory(base_currency, quote_currency, timestamp)

        elif is_fiat(base_currency) and is_fiat(quote_currency):
            return self._get_exchange_rate_from_ratesapi(base_currency, quote_currency, timestamp)

        return None

    def get_implicit_exchange_rate(self, base_currency, quote_currency, rate, timestamp):
        return ExchangeRate(base_currency, quote_currency, rate, timestamp, self._sources['implicit'])

    def _get_exchange_rate_from_memory(self, base_currency, quote_currency, timestamp):
        """
        Searches in memory for a rate.
        """

        a = base_currency
        b = quote_currency

        if a not in self._exchange_rates:
            a, b = b, a
            if a not in self._exchange_rates:
                return None

        if b not in self._exchange_rates[a]:
            return None

        closest_timestamp = min(self._exchange_rates[a][b].keys(),
                                key=lambda found_timestamp: abs(found_timestamp - timestamp))

        max_days = 1

        age = abs(closest_timestamp - timestamp)
        if age > timedelta(days=max_days):
            logging.info(f'warning: closest exchange rate found {base_currency}/{quote_currency} '
                         f'for {date_to_string(timestamp)} '
                         f'is from {date_to_string(closest_timestamp)} '
                         f'({age.days} day(s))')

        return self._exchange_rates[a][b][closest_timestamp]

    def _query_exchange_rates_from_cryptocompare(self, base_currency, quote_currency):
        """
        Queries crypto exchange rates via "Historical Daily OHLCV" from cryptocompare.com using 'cryptocompy' library
        (see https://min-api.cryptocompare.com/ and https://github.com/ttsteiger/cryptocompy)
        The results are cachend in the internal exchange rates data.
        Every currency pair will only be queried once.
        """

        marker = f'{base_currency}/{quote_currency}'

        if marker in self._cryptocompare_already_queried:
            return

        day_count = (self._date_to - self._date_from).days
        to_ts = int(self._date_to.timestamp())
        logging.info(f'querying cryptocompare.com exchange rates {base_currency}/{quote_currency} '
                     f'for {self._tax_year}')
        result = price.get_historical_data(base_currency, quote_currency, 'day', to_ts=to_ts, limit=day_count)
        logging.info(f'got {len(result)} OHLCV values')
        time.sleep(2)

        if len(result) > 0:

            if base_currency not in self._exchange_rates:
                self._exchange_rates[base_currency] = {}

            if quote_currency not in self._exchange_rates[base_currency]:
                self._exchange_rates[base_currency][quote_currency] = {}

            for data in result:

                rate = value_to_decimal(data['close'])
                timestamp = parse_date(data['time'])
                exchange_rate = ExchangeRate(base_currency, quote_currency, rate, timestamp,
                                             self._sources['cryptocompare'])
                self._exchange_rates[base_currency][quote_currency][timestamp] = exchange_rate

        self._cryptocompare_already_queried.append(marker)

    def _get_exchange_rate_from_ratesapi(self, base_currency, quote_currency, timestamp):
        """
        Queries fiat exchange rate from https://ratesapi.io/api/ using 'forex-python' library.
        (see https://github.com/MicroPyramid/forex-python)
        """

        logging.info(f'querying ratesapi.io for exchange rate {base_currency}/{quote_currency} '
                     f'at {date_to_string(timestamp)}')

        try:
            rate = CurrencyRates(force_decimal=True).get_rate(base_currency, quote_currency, date_obj=timestamp)
            time.sleep(1)
            if rate is None:
                return None
            logging.info(f'Got one result')
        except RatesNotAvailableError as e:
            raise e

        return ExchangeRate(base_currency, quote_currency, rate, timestamp, self._sources['ratesapi'])

    def load_exchange_rates_from_configured_files(self, configuration):
        """
        Loads all exchange rate files specified by the configuration.
        """

        sections = configuration.get('exchange-rate-files', default=[])
        for section in sections:
            self.load_exchange_rates_from_configured_file(section)

    def load_exchange_rates_from_configured_file(self, section):
        """
        Loads the exchange rate file specified by the configuration section.
        """

        source_id = section['id']
        short_description = section['short-description']
        long_description = section['long-description']
        file = section['file']
        delimiter = section['delimiter']
        encoding = section['encoding']
        quotechar = section['quotechar']
        empty_marker = section['empty-marker']
        base_currency = section['base-currency']

        if source_id in self._sources:
            raise ExchangeRateImportError(f'source with id "{source_id}" is already defined')

        source = ExchangeRateSource(source_id, short_description, long_description)
        self._sources[source_id] = source

        if base_currency not in self._exchange_rates:
            self._exchange_rates[base_currency] = {}

        logging.info(f'importing exchange rate source {source_id} from {file}')

        rates = self._exchange_rates[base_currency]

        with open(file, 'rt', encoding=encoding) as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter, quotechar=quotechar)

            row_count = 0
            header = None

            for row in reader:

                row_count += 1

                if header is None:  # first row must always be header
                    header = row
                    continue

                timestamp = parse_date(row[0])
                if (timestamp < self._date_from) or (timestamp >= self._date_to):
                    continue  # skip rows where date is outside tax year

                col_count = 0
                for quote_currency in header:
                    if col_count != 0:
                        exchange_rate = row[col_count].strip()
                        if exchange_rate and exchange_rate != empty_marker:
                            if quote_currency not in rates:
                                rates[quote_currency] = {}
                            exchange_rate_decimal = value_to_decimal(exchange_rate)
                            rates[quote_currency][timestamp] = ExchangeRate(base_currency, quote_currency,
                                                                            exchange_rate_decimal, timestamp, source)
                    col_count += 1
