import logging
from decimal import Decimal

import ccxt

from src.ColumnReader import column_reader
from src.DateUtils import parse_date, get_start_of_year, get_start_of_year_after
from src.bo.Order import Order
from src.bo.Trade import Trade
from src.bo.Transaction import Transaction, TransactionType


def get_exchange(exchange_id):
    """
    Returns the exchange corresponding to the section ID.
    :raise: error, if the exchange ID is not a valid ccxt exchange ID
    """
    if exchange_id not in ccxt.exchanges:
        raise Exception(f'configured exchange id "[{exchange_id}]" is invalid, '
                        f'valid exchange ids are: {ccxt.exchanges}')
    return getattr(ccxt, exchange_id)()


class CsvOrderImporter(object):
    """
    Imports orders from CSV files.
    """

    def __init__(self, configuration) -> None:
        super().__init__()

        self._configuration = configuration
        self._tax_year = configuration.get_mandatory('tax-year')
        self._date_from = get_start_of_year(self._tax_year)
        self._date_to = get_start_of_year_after(self._tax_year)

    def import_orders(self):

        orders = []

        sections = self._configuration.get('files', default=[])
        for section in sections:

            exchange_id = section['exchange']
            exchange = get_exchange(exchange_id)
            exchange.load_markets()
            files = section['files']

            for file in files:

                logging.info(f'importing trades from file {file}')
                with column_reader(section, file) as reader:
                    for column in reader:
                        trade = self.get_trade(column)
                        order = Order(trade.source_id, exchange_id)
                        order.trades = [trade]
                        orders.append(order)

        return orders

    def get_trade(self, column):
        """
        Extracts a trade with three transactions (BUY, SELL, FEE) from the specified column.
        """

        timestamp = parse_date(column.get('date'))
        if (timestamp < self._date_from) or (timestamp >= self._date_to):
            return None  # skip rows where date is outside tax year

        transactions = []

        base = Transaction()
        base.currency = column.get_currency('base-currency')
        base.timestamp = timestamp
        base.amount = Decimal(column.get('base')).copy_abs()
        transactions.append(base)

        quote = Transaction()
        quote.currency = column.get_currency('quote-currency')
        quote.timestamp = timestamp
        quote.amount = base.amount * Decimal(column.get('price')).copy_abs()
        transactions.append(quote)

        fee = Transaction()
        fee.currency = column.get_currency('fee-currency')
        fee.timestamp = timestamp
        fee.amount = Decimal(column.get('fee')).copy_abs()
        transactions.append(fee)

        sell_indicator = column.get('sell-indicator', empty_allowed=True)
        if sell_indicator is not None:
            base.type = TransactionType.SELL
            quote.type = TransactionType.BUY
            fee.type = TransactionType.FEE
        else:
            base.type = TransactionType.BUY
            quote.type = TransactionType.SELL
            fee.type = TransactionType.FEE

        # sort by type
        transactions = sorted(transactions, key=lambda transaction: transaction.type.value)

        return Trade(column.get('id'), timestamp, transactions)
