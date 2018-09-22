import logging
import os
import sys
import time

import ccxt
import sqlalchemy
from ccxt import NetworkError
from sqlalchemy.orm import sessionmaker

from src.BalanceQueue import BalanceQueue, QueueType
from src.CcxtOrderImporter import CcxtOrderImporter
from src.CsvOrderImporter import CsvOrderImporter
from src.ExchangeRates import ExchangeRates
from src.bo.Base import Base
from src.bo.ExchangeRateSource import ExchangeRateSource
from src.bo.Order import Order, sort_by_time
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
            except NetworkError:
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
    Updates orders in DB, returns orders that were identified as new.
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


def load_orders(session):
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
                    transaction.converted_amount = transaction.amount
                    continue

                if transaction.type == TransactionType.BUY:  # no converted amount needed
                    transaction.exchange_rate = None
                    transaction.converted_amount = None
                    continue

                exchange_rate = exchange_rates.get_exchange_rate(transaction.currency, tax_currency, trade.timestamp)
                if exchange_rate is None:
                    # this HAS to be a fatal error: without exchange rate, we cannot calculate tax
                    raise MissingDataError(f'no exchange rate found for transaction {transaction}')

                transaction.exchange_rate = exchange_rate
                transaction.converted_amount = transaction.amount * exchange_rate.get_rate(transaction.currency,
                                                                                           tax_currency)

    session.add_all(orders)
    session.commit()


# noinspection PyUnusedLocal TODO
def calculate_profit_loss(orders, configuration):
    """
    Calculates profit / loss from trades.
    """

    tax_currency = configuration.get_mandatory('tax-currency')
    queue = BalanceQueue(tax_currency, QueueType.FIFO)

    date_from = configuration.get_date_from()
    date_to = configuration.get_date_to()

    logging.info(f'date / time, '
                 f'transaction id, '
                 f'sell amount, '
                 f'sell currency, '
                 f'sell exchange rate, '
                 f'sell exchange rate date / time, '
                 f'sell exchange rate source, '
                 f'sell value in {tax_currency}, '
                 f'buy amount, '
                 f'buy currency, '
                 f'buy exchange rate, '
                 f'buy exchange rate date / time, '
                 f'buy exchange rate source, '
                 f'buy value in {tax_currency}, '
                 f'fee amount, '
                 f'fee currency, '
                 f'fee exchange rate, '
                 f'fee exchange rate date / time, '
                 f'fee exchange rate source, '
                 f'fee value in {tax_currency}, '
                 f'FIFO entries, '
                 f'cost {tax_currency}, '
                 f'buying fees {tax_currency}, '
                 f'cost + buying fees {tax_currency}, '
                 f'proceeds {tax_currency}, '
                 f'selling fees {tax_currency}, '
                 f'proceeds + selling fees {tax_currency}, '
                 f'profit / loss {tax_currency}')

    # TODO go through all trades and output the preceding information (see #12)
