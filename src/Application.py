import logging
import os
import sys
import time
from decimal import Decimal

import ccxt
import sqlalchemy
from ccxt import NetworkError
from sqlalchemy.orm import sessionmaker

from src.CcxtOrderImporter import CcxtOrderImporter
from src.CsvOrderImporter import CsvOrderImporter
from src.DateUtils import date_to_simple_string_with_time
from src.Error import Error
from src.ExchangeRates import ExchangeRates
from src.MultiCurrencyBalanceQueue import MultiCurrencyBalanceQueue
from src.NumberUtils import currency_to_string
from src.bo.Base import Base
from src.bo.ExchangeRateSource import ExchangeRateSource
from src.bo.Order import Order, sort_by_time
from src.bo.Trade import get_earliest_time
from src.bo.Transaction import TransactionType


class MissingDataError(Exception):
    """
    Signals an error while finding exchange rates.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)


def get_working_dir():
    """
    Returns the directory where the application data is to be read and stored.
    """
    if getattr(sys, 'frozen', False):
        # ToDo: this returns path to executable, not working directory
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.getcwd()


def init_logging(configuration):
    """
    Initializes logging
    """

    filename = configuration.get('logging', 'filename')
    level_file = configuration.get('logging', 'level-file')
    level_console = configuration.get('logging', 'level-console')

    root_logger = logging.getLogger()

    file_handler = logging.FileHandler(os.path.join(get_working_dir(), filename))
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)-4.4s] %(message)s"))
    file_handler.setLevel(eval(f'logging.{level_file}'))
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    console_handler.setLevel(eval(f'logging.{level_console}'))
    root_logger.addHandler(console_handler)

    root_logger.setLevel(logging.DEBUG)

    logging.info('logging started')


def init_db(configuration):
    """
    Creates a DB session.
    """
    url = configuration.get_mandatory('database', 'url')
    engine = sqlalchemy.create_engine(url, echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def query_transactions(configuration):
    """
    Queries the configured exchanges for orders.
    :return: list of all orders
    """

    orders = []

    for exchange_id in configuration.get('exchanges', default={}):
        if exchange_id not in ccxt.exchanges:
            raise Exception(f'Configured section [{exchange_id}] is not a valid exchange id. '
                            f'Valid exchange ids are: {ccxt.exchanges}')
        exchange = getattr(ccxt, exchange_id)()
        exchange.apiKey = configuration.get_mandatory('exchanges', exchange_id, 'key')
        exchange.secret = configuration.get_mandatory('exchanges', exchange_id, 'secret')
        symbols = configuration.get('exchanges', exchange_id, 'symbols', default=None)
        date_from = configuration.get_date_from()
        date_to = configuration.get_date_to()
        while True:
            try:
                orders.extend(CcxtOrderImporter(exchange).fetch_orders(date_from, date_to, symbols=symbols))
                break
            except NetworkError as e:
                retry_interval = configuration.get('retry-interval')
                logging.error(f'Network error. Retrying in {retry_interval}s.')
                time.sleep(retry_interval)

    return orders


def import_files(configuration):
    """
    Import trades from configured files.
    """
    return CsvOrderImporter(configuration).import_orders()


def update_orders(session, received_orders):
    """
    Updates orders in DB, returns orders that were identified as new
    """

    stored_orders = session.query(Order)
    new_orders = set(received_orders).difference(stored_orders)
    session.add_all(new_orders)
    session.commit()
    return new_orders


def delete_transaction_data(session):
    """
    Deletes all the transaction-related data that was imported.
    """
    session.query(Order).delete()
    session.commit()
    logging.info('deleted all transaction data from DB')
    pass


def delete_exchange_rate_data(session):
    """
    Deletes all the exchange-rate-related data that was imported.
    """
    session.query(ExchangeRateSource).delete()
    session.commit()
    logging.info('deleted all exchange rate data from DB')
    pass


def save_orders(session, received_orders):
    """
    Persists the specified orders in the DB.
    """

    new_orders = update_orders(session, received_orders)
    received_count = len(received_orders)
    new_count = len(new_orders)
    previous_count = received_count - new_count
    logging.info(f'received {received_count} orders, '
                 f'{previous_count} already present, '
                 f'{new_count} added')


def load_orders(session, configuration):
    """
    Retrieves all transaction groups in the specified time range.
    """

    return sort_by_time(session.query(Order))


def find_exchange_rates(session, orders, configuration):
    """
    Queries the exchange rates from base / quote currency to tax currency at the time of the transaction group
    and updates all groups accordingly.
    """

    tax_currency = configuration.get_mandatory('tax-currency')
    exchange_rates = ExchangeRates(configuration)

    for order in orders:
        for trade in order.trades:
            for transaction in trade.transactions:

                if transaction.currency == tax_currency:  # no conversion needed
                    transaction.exchange_rate = None
                    transaction.taxable_amount = transaction.amount
                    continue

                if transaction.type == TransactionType.BUY:  # no taxable amount needed
                    transaction.exchange_rate = None
                    transaction.taxable_amount = None
                    continue

                exchange_rate = exchange_rates.get_exchange_rate(transaction.currency, tax_currency, trade.timestamp)
                if exchange_rate is None:
                    # this HAS to be a fatal error: without exchange rate, we cannot calculate tax
                    raise MissingDataError(f'no exchange rate found for transaction {transaction}')

                transaction.exchange_rate = exchange_rate
                transaction.taxable_amount = transaction.amount * exchange_rate.get_rate(transaction.currency,
                                                                                         tax_currency)

    session.add_all(orders)
    session.commit()


def calculate_profit_loss(orders, configuration):
    """
    Calculates profit / loss from transactions.
    """

    tax_currency = configuration.get_mandatory('tax-currency')
    queue = MultiCurrencyBalanceQueue(tax_currency)

    date_from = configuration.get_date_from()
    date_to = configuration.get_date_to()

    logging.info(f'date, '
                 f'exchange, '
                 f'buy amount, '
                 f'buy currency, '
                 f'sell amount, '
                 f'sell currency, '
                 f'sell amount (in tax currency), '
                 f'tax currency, '
                 f'fee, '
                 f'fee currency, '
                 f'fee (in tax currency), '
                 f'tax currency')

    for order in orders:

        buy_transactions = get_transactions_of_type(order, TransactionType.BUY)
        sell_transactions = get_transactions_of_type(order, TransactionType.SELL)
        fee_transactions = get_transactions_of_type(order, TransactionType.FEE)

        buy_amount = sum_attribute(buy_transactions, lambda transaction: transaction.amount)
        buy_currency = buy_transactions[0].currency

        sell_amount = sum_attribute(sell_transactions, lambda transaction: transaction.amount)
        sell_taxable_amount = sum_attribute(sell_transactions, lambda transaction: transaction.taxable_amount)
        sell_currency = sell_transactions[0].currency

        fee_amount = sum_attribute(fee_transactions, lambda transaction: transaction.amount)
        fee_taxable_amount = sum_attribute(fee_transactions, lambda transaction: transaction.taxable_amount)
        fee_currency = fee_transactions[0].currency

        timestamp = date_to_simple_string_with_time(get_earliest_time(order.trades))

        logging.info(f'{timestamp}, '
                     f'{order.exchange}, '
                     f'{currency_to_string(buy_amount, buy_currency, True)}, '
                     f'{buy_currency}, '
                     f'{currency_to_string(sell_amount, sell_currency, True)}, '
                     f'{sell_currency}, '
                     f'{currency_to_string(sell_taxable_amount, tax_currency, True)}, '
                     f'{tax_currency}, '
                     f'{currency_to_string(fee_amount, fee_currency, True)}, '
                     f'{fee_currency}, '
                     f'{currency_to_string(fee_taxable_amount, tax_currency, True)}, '
                     f'{tax_currency}')


def sum_attribute(transactions, accessor):
    value = Decimal(0)
    for transaction in transactions:
        value += accessor(transaction)

    return value


def get_transactions_of_type(order, transaction_type):
    transactions = []
    currency = None
    for trade in order.trades:
        for transaction in trade.transactions:
            if transaction.type == transaction_type:

                if currency is None:
                    currency = transaction.currency
                else:
                    if transaction.currency != currency:
                        raise Error(f'differing currencies found '
                                    f'in transactions of type {transaction_type.name} '
                                    f'in trade {trade.source_id} '
                                    f'of order {order.source_id}')

                transactions.append(transaction)

    return transactions
