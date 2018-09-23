import logging
import os
import sys
import time
from decimal import Decimal

import ccxt
import sqlalchemy
from ccxt import NetworkError
from sqlalchemy.orm import sessionmaker

from src.BalanceQueue import BalanceQueue, QueueType
from src.CcxtOrderImporter import CcxtOrderImporter
from src.CsvOrderImporter import CsvOrderImporter
from src.DateUtils import get_start_of_year, get_start_of_year_after, date_and_time_to_string
from src.ExchangeRates import ExchangeRates
from src.NumberUtils import currency_to_string
from src.bo.Base import Base
from src.bo.ExchangeRateSource import ExchangeRateSource
from src.bo.Order import Order, sort_orders_by_time
from src.bo.Trade import Trade
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
        tax_year = configuration.get_mandatory('tax-year')
        date_from = get_start_of_year(tax_year)
        date_to = get_start_of_year_after(tax_year)
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
    Retrieves all orders.
    """

    return session.query(Order)


def load_trades(session):
    """
    Retrieves all trades.
    """

    return session.query(Trade)


def find_exchange_rates(session, orders, configuration):
    """
    Queries the exchange rates from base / quote currency to tax currency at time of order
    and updates all orders accordingly.
    """

    orders = sort_orders_by_time(orders)

    tax_currency = configuration.get_mandatory('tax-currency')
    exchange_rates = ExchangeRates(configuration)

    for order in orders:
        for trade in order.trades:

            buy = trade.get_transaction(TransactionType.BUY)
            sell = trade.get_transaction(TransactionType.SELL)

            implicit_exchange_rate = exchange_rates.get_implicit_exchange_rate(buy.currency, sell.currency,
                                                                               buy.amount / sell.amount,
                                                                               trade.timestamp)

            for transaction in trade.transactions:

                # use the trade's exchange rate if possible
                if implicit_exchange_rate.can_convert(transaction.currency, tax_currency):
                    exchange_rate = implicit_exchange_rate
                else:
                    exchange_rate = exchange_rates.get_exchange_rate(transaction.currency, tax_currency,
                                                                     transaction.timestamp)

                if exchange_rate is None:
                    # this HAS to be a fatal error: without exchange rate, we cannot calculate tax
                    raise MissingDataError(f'no exchange rate found for transaction {transaction}')

                transaction.exchange_rate = exchange_rate
                transaction.converted_amount = transaction.amount * exchange_rate.get_rate(transaction.currency,
                                                                                           tax_currency)

    session.add_all(orders)
    session.commit()


def calculate_profit_loss(orders, configuration, output_file):
    """
    Calculates and outputs profit / loss from trades (and related data).
    """

    if output_file is not None:
        pass

    orders = sort_orders_by_time(orders)

    tax_currency = configuration.get_mandatory('tax-currency')

    logging.info(f'date / time, '
                 f'order id, '
                 f'trade id, '
                 f'sell amount, '
                 f'sell currency, '
                 f'sell exchange rate vs {tax_currency}, '
                 f'sell exchange rate date / time, '
                 f'sell exchange rate source, '
                 f'sell value in {tax_currency}, '
                 f'buy amount, '
                 f'buy currency, '
                 f'buy exchange rate vs {tax_currency}, '
                 f'buy exchange rate date / time, '
                 f'buy exchange rate source, '
                 f'buy value in {tax_currency}, '
                 f'fee amount, '
                 f'fee currency, '
                 f'fee exchange rate vs {tax_currency}, '
                 f'fee exchange rate date / time, '
                 f'fee exchange rate source, '
                 f'fee value in {tax_currency}, '
                 f'FIFO entries, '
                 f'cost {tax_currency}, '
                 f'buying fees {tax_currency}, '
                 f'cost + buying fees {tax_currency}, '
                 f'proceeds {tax_currency}, '
                 f'selling fees {tax_currency}, '
                 f'proceeds - selling fees {tax_currency}, '
                 f'profit / loss {tax_currency}')

    queue = BalanceQueue(tax_currency, QueueType.FIFO)

    for order in orders:
        for trade in order.trades:

            sell_info = queue.trade(trade)

            sell = trade.get_transaction(TransactionType.SELL)
            buy = trade.get_transaction(TransactionType.BUY)
            fee = trade.get_transaction(TransactionType.FEE)

            logging.info(f'{date_and_time_to_string(trade.timestamp)}, '
                         f'{order.id}, '
                         f'{trade.id}, '
                         f'{currency_to_string(sell.amount, sell.currency)}, '
                         f'{sell.currency}, '
                         f'{exchange_rate_to_string(sell, tax_currency)}, '
                         f'{date_and_time_to_string(sell.exchange_rate.timestamp)}, '
                         f'{sell.exchange_rate.source.short_description}, '
                         f'{currency_to_string(sell.converted_amount, tax_currency)}, '
                         f'{currency_to_string(buy.amount, buy.currency)}, '
                         f'{buy.currency}, '
                         f'{exchange_rate_to_string(buy, tax_currency)}, '
                         f'{date_and_time_to_string(buy.exchange_rate.timestamp)}, '
                         f'{buy.exchange_rate.source.short_description}, '
                         f'{currency_to_string(buy.converted_amount, tax_currency)}, '
                         f'{currency_to_string(fee.amount, fee.currency)}, '
                         f'{fee.currency}, '
                         f'{exchange_rate_to_string(fee, tax_currency)}, '
                         f'{date_and_time_to_string(fee.exchange_rate.timestamp)}, '
                         f'{fee.exchange_rate.source.short_description}, '
                         f'{currency_to_string(fee.converted_amount, tax_currency)}, '
                         f'{buy_items_to_string(sell_info)}, '
                         f'{currency_to_string(sell_info.cost, tax_currency)}, '
                         f'{currency_to_string(sell_info.buying_fees, tax_currency)}, '
                         f'{currency_to_string(sell_info.cost + sell_info.buying_fees, tax_currency)}, '
                         f'{currency_to_string(sell_info.proceeds, tax_currency)}, '
                         f'{currency_to_string(sell_info.selling_fees, tax_currency)}, '
                         f'{currency_to_string(sell_info.proceeds - sell_info.selling_fees, tax_currency)}, '
                         f'{currency_to_string(sell_info.pl, tax_currency)}, '
                         f'')


def exchange_rate_to_string(transaction, tax_currency):
    """
    Returns a string representation of the transaction's exchange rate.
    """
    exchange_rate = transaction.exchange_rate.get_rate(transaction.currency, tax_currency)
    return currency_to_string(exchange_rate, tax_currency)


def buy_items_to_string(sell_info):
    """
    Returns a string repesentation of all the buy trades that were associated with the sale and
    some additional info like ID of buy trade, percent of sold amount attributed to buy trade and
    amount attributed to buy trade.
    """
    buy_items = sell_info.buy_items

    out = []

    for buy_item in buy_items:

        if buy_item.trade is not None:
            trade_id = f'#{buy_item.trade.id}'
        else:
            trade_id = "unaccounted"

        percent = round(buy_item.amount / sell_info.amount * Decimal('100'), 0)
        percent_string = f'{percent}%'

        currency = sell_info.sell_trade.get_transaction(TransactionType.SELL).currency
        amount_string = currency_to_string(buy_item.amount, currency, True)

        out.append(f'[{trade_id}|{percent_string}|{amount_string}]')

    return ' '.join(out)
