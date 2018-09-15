import logging
import time
from _decimal import Decimal
from math import ceil

from src.DateUtils import parse_date
from src.bo.Order import Order
from src.bo.Trade import Trade
from src.bo.Transaction import Transaction, TransactionType


def import_orders(trades_raw, exchange_name, date_from, date_to, currency_lookup_func):
    """
    Returns a list of orders based on the specified trades.
    :param: a lookup function that takes a market symbol as first parameter
            and 'base'/'quote' as second parameter and returns a currency symbol
    """

    orders = {}

    for trade_raw in trades_raw:

        timestamp = parse_date(trade_raw['datetime'])
        if (timestamp < date_from) or (timestamp >= date_to):
            continue  # skip trades outside tax year

        transactions = []
        symbol = trade_raw['symbol']

        base = Transaction()
        base.type = TransactionType.BUY if trade_raw['side'] == 'buy' else TransactionType.SELL
        base.currency = currency_lookup_func(symbol, 'base')
        base.timestamp = timestamp
        base.amount = Decimal(str(trade_raw['amount']))
        transactions.append(base)

        quote = Transaction()
        quote.type = TransactionType.SELL if trade_raw['side'] == 'buy' else TransactionType.BUY
        quote.currency = currency_lookup_func(symbol, 'quote')
        quote.timestamp = timestamp
        quote.amount = Decimal(str(trade_raw['amount'])) * Decimal(str(trade_raw['price']))
        transactions.append(quote)

        fee = Transaction()
        fee.type = TransactionType.FEE
        fee.currency = trade_raw['fee']['currency']
        fee.timestamp = timestamp
        fee.amount = Decimal(str(trade_raw['fee']['cost']))
        transactions.append(fee)

        # sort by type
        transactions = sorted(transactions, key=lambda transaction: transaction.type.value)

        order_id = trade_raw['order']

        if order_id not in orders:
            orders[order_id] = Order(order_id, exchange_name)
        order = orders[order_id]

        trade = Trade(trade_raw['id'], timestamp, transactions)
        order.trades.append(trade)

    return list(orders.values())


class CcxtOrderImporter:
    """
    Imports orders using ccxt's unified API
    """

    def __init__(self, exchange):
        self._exchange = exchange
        self._exchange.load_markets()  # self.exchange.verbose = True

    def fetch_orders(self, date_from, date_to, symbols=None):
        """
        Imports orders for the specified symbols.
        Some exchanges such as Bitfinex will only respond with transactions for the specified symbols.
        Others such as Kraken will respond with transcations for all symbols.
        """

        logging.info(f'exchange: {self._exchange.id}')

        orders = []

        if symbols is None:

            new_orders = import_orders(self._exchange.fetch_my_trades(), self._exchange.markets, self._exchange.id,
                                       date_from, date_to)
            orders.extend(new_orders)

        else:

            symbols_to_query = set(self._exchange.symbols).intersection(symbols)
            polling_rate = ceil(self._exchange.rateLimit / 1000)

            for symbol in symbols_to_query:
                new_orders = import_orders(self._exchange.fetch_my_trades(symbol), self._exchange.markets,
                                           self._exchange.id, date_from, date_to)
                logging.info(f'received orders for market {symbol}: {len(new_orders)}')
                orders.extend(new_orders)
                time.sleep(polling_rate)

        logging.info(f'orders received total: {len(orders)}')

        return orders

    def _lookup_currency(self, symbol, currency_type):
        return self._exchange.markets[symbol][currency_type]
