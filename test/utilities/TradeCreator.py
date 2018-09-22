from decimal import Decimal

from src.bo.Trade import Trade
from src.bo.Transaction import Transaction, TransactionType


class TradeCreator:
    """
    Can be used to create trades for unit tests.
    """

    def __init__(self, tax_currency, exchange_rates) -> None:

        self.tax_currency = tax_currency
        self.exchange_rates = dict(exchange_rates)

    def set_tax_exchange_rate(self, currency, rate):
        """
        Sets the exchange rate from tax currency to the specified currency (with tax currency as base currency).
        """
        self.exchange_rates[currency] = rate

    def get_tax_exchange_rate(self, currency):
        """
        Returns an exchange rate from tax currency to the specified currency (with tax currency as base currency).
        """

        if currency == self.tax_currency:
            return Decimal(1.0)
        return Decimal(self.exchange_rates[currency])

    def create_trade(self, transaction_data):
        """
        Creates a trade with transactions corresponding to the input values.
        The converted amount is calcualated, using a fixed tax currency (EUR) and fixed exchange rates.
        :return: trade object
        """

        transactions = []

        sell = Transaction()
        sell.type = TransactionType.SELL
        sell.currency = transaction_data['sell'][0]
        sell.amount = Decimal(transaction_data['sell'][1])
        sell.converted_amount = sell.amount * self.get_tax_exchange_rate(sell.currency)
        transactions.append(sell)

        buy = Transaction()
        buy.type = TransactionType.BUY
        buy.currency = transaction_data['buy'][0]
        buy.amount = Decimal(transaction_data['buy'][1])
        buy.converted_amount = buy.amount * self.get_tax_exchange_rate(buy.currency)
        transactions.append(buy)

        fee = Transaction()
        fee.type = TransactionType.FEE
        fee.currency = transaction_data['fee'][0]
        fee.amount = Decimal(transaction_data['fee'][1])
        fee.converted_amount = fee.amount * self.get_tax_exchange_rate(fee.currency)
        transactions.append(fee)

        return Trade(None, None, transactions)
