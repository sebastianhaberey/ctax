import os
from datetime import datetime
from decimal import Decimal
from unittest import TestCase

from dateutil.tz import UTC

from src.Configuration import Configuration
from src.ExchangeRates import ExchangeRates

TESTDATA_DATA_FILE_1 = os.path.join(os.path.dirname(__file__), 'testdata', 'test-exchange-rates-1.csv')
TESTDATA_DATA_FILE_2 = os.path.join(os.path.dirname(__file__), 'testdata', 'test-exchange-rates-2.csv')

TESTDATA_CONFIGURATION = """

  tax-year: 2018
  query-exchange-rate-apis: False
  exchange-rate-files:

    - id: 'test-file-1'
      file: '${FILENAME1}'
      description: 'some description'
      base-currency: 'EUR'
      delimiter: ','
      quotechar: '"'
      encoding: 'utf8'
      empty-marker: 'N/A'

    - id: 'test-file-2'
      file: '${FILENAME2}'
      description: 'some other description'
      base-currency: 'EUR'
      delimiter: ','
      quotechar: '"'
      encoding: 'utf8'
      empty-marker: 'N/A'
      
"""


class TestExchangeRates(TestCase):
    """
    The two test exchange rates in the file are:

        2018-05-10 00:00:00.000000 UTC -> 1.1878
        2018-05-11 00:00:00.000000 UTC -> 1.1934

    """

    def setUp(self):
        document = TESTDATA_CONFIGURATION
        document = document.replace('${FILENAME1}', TESTDATA_DATA_FILE_1)
        document = document.replace('${FILENAME2}', TESTDATA_DATA_FILE_2)
        self.configuration = Configuration(document)
        self.exchange_rates = ExchangeRates(self.configuration)

    def test_get_exchange_rate(self):
        rate = self.exchange_rates.get_exchange_rate('EUR', 'USD', datetime(2000, 1, 1, tzinfo=UTC))
        self.assertEqual(Decimal('1.1878'), rate.rate)
        rate = self.exchange_rates.get_exchange_rate('EUR', 'USD', datetime(2018, 5, 10, tzinfo=UTC))
        self.assertEqual(Decimal('1.1878'), rate.rate)
        rate = self.exchange_rates.get_exchange_rate('EUR', 'USD', datetime(2018, 5, 10, 12, tzinfo=UTC))
        self.assertEqual(Decimal('1.1878'), rate.rate)
        rate = self.exchange_rates.get_exchange_rate('EUR', 'USD', datetime(2018, 5, 10, 12, 0, 0, 1, tzinfo=UTC))
        self.assertEqual(Decimal('1.1934'), rate.rate)
        rate = self.exchange_rates.get_exchange_rate('EUR', 'USD', datetime(2018, 5, 11, tzinfo=UTC))
        self.assertEqual(Decimal('1.1934'), rate.rate)
        rate = self.exchange_rates.get_exchange_rate('EUR', 'USD', datetime(2100, 1, 1, tzinfo=UTC))
        self.assertEqual(Decimal('1.1934'), rate.rate)

    def test_get_exchange_rate_inverse(self):
        rate = self.exchange_rates.get_exchange_rate('USD', 'EUR', datetime(2018, 5, 10, 12, tzinfo=UTC))
        self.assertEqual(Decimal('1.1878'), rate.rate)
        rate = self.exchange_rates.get_exchange_rate('USD', 'EUR', datetime(2018, 5, 10, 12, 0, 0, 1, tzinfo=UTC))
        self.assertEqual(Decimal('1.1934'), rate.rate)

    def test_exchange_rate_attributes(self):

        rate = self.exchange_rates.get_exchange_rate('EUR', 'USD', datetime(2018, 5, 10, tzinfo=UTC))

        self.assertEqual('EUR', rate.base_currency)
        self.assertEqual('USD', rate.quote_currency)
        self.assertEqual(Decimal('1.1878'), rate.rate)
        self.assertEqual(datetime(2018, 5, 10, tzinfo=UTC), rate.timestamp)
        source = rate.source
        self.assertEqual('test-file-1', source.source_id)
        self.assertEqual('some description', source.description)