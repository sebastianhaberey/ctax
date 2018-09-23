from decimal import Decimal
from functools import reduce

from src.NumberUtils import currency_to_string
from src.bo.Transaction import TransactionType


class SellInfo:
    """
    Information about a sell action, such as cost / proceeds, profit / loss, etc.
    """

    def __init__(self, sell_trade, buy_items):
        self.sell_trade = sell_trade  # the trade representing the sale
        self.buy_items = buy_items  # list of buys from the past associated with the sale

    @property
    def amount(self):
        """
        The amount sold (in original currency).
        """
        return self.sell_trade.get_transaction(TransactionType.SELL).amount

    @property
    def cost(self):
        """
        Cost when buying (in tax currency).
        """

        return reduce(lambda a, b: a + b.cost, self.buy_items, Decimal(0))  # summarize cost of all buy items

    @property
    def buying_fees(self):
        """
        Buying fees (in tax currency).
        """

        return reduce(lambda a, b: a + b.fee, self.buy_items, Decimal(0))  # summarize fees of all buy items

    @property
    def proceeds(self):
        """
        Proceeds when selling (in tax currency).
        """
        return self.sell_trade.get_transaction(TransactionType.SELL).converted_amount

    @property
    def selling_fees(self):
        """
        Selling fees (in tax currency).
        """
        return self.sell_trade.get_transaction(TransactionType.FEE).converted_amount

    @property
    def pl(self):
        """
        Profit / loss of the sale (in tax currency).
        This is calculated by subtracting the cost of purchase from the proceeds.
        If any part of the amount that was sold could not be accounted for with a corresponding buy action,
        that means the cost of purchase for that part was zero, and the profit for that part was 100 percent.
        """
        return (self.proceeds - self.selling_fees) - (self.cost + self.buying_fees)

    def render(self, currency, tax_currency):
        out = f'total: ' \
              f'sold {currency_to_string(self.amount, currency)} ' \
              f'cost {currency_to_string(self.cost, tax_currency)}, ' \
              f'proceeds {currency_to_string(self.proceeds, tax_currency)} ' \
              f'P/L: {currency_to_string(self.pl, tax_currency)}'
        return out
