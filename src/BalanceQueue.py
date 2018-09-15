from collections import deque
from decimal import Decimal
from enum import Enum

from src.NumberUtils import currency_to_string


class QueueType(Enum):
    """
    Type of queue.
    """
    FIFO = 0
    LIFO = 1


class BalanceQueue:
    """
    Queue that keeps a tab of amounts bought, their price, and the current balance.
    When an amount is sold, its initial cost is calculated by FIFO (default) or LIFO principle.
    If the initial cost cannot be fully determined (because there is not enough balance in the queue),
    the amount that cannot be accounted for will be determined as well.
    """

    def __init__(self, queue_type=QueueType.FIFO):
        self.queue_type = queue_type
        self.deque = deque()

    def buy(self, amount_bought, price_bought):
        if amount_bought == Decimal('0'):
            return Decimal('0')
        item = Item(amount_bought, price_bought)
        self.deque.append(item)
        return BuyResult(item)

    def sell(self, amount_sold, price_sold):

        remainder = amount_sold
        items_bought = []

        while remainder > Decimal('0'):

            if self.is_empty():
                break

            item = self.pop()

            if remainder < item.amount:
                items_bought.append(Item(remainder, item.price))
                item.amount -= remainder
                self.put_back(item)
                remainder = Decimal('0')
                break
            elif remainder >= item.amount:
                items_bought.append(item)
                remainder -= item.amount

        return SellResult(amount_sold, price_sold, items_bought, remainder)

    def fee(self, amount, exchange_rate):
        return FeeResult(self.sell(amount, exchange_rate))

    def get_balance(self):
        balance = Decimal('0')
        for expense in self.deque:
            balance += expense.amount
        return balance

    def is_empty(self):
        return len(self.deque) == 0

    def pop(self):
        if self.queue_type == QueueType.FIFO:
            item = self.deque.popleft()
        else:
            item = self.deque.pop()
        return item

    def put_back(self, item):
        if self.queue_type == QueueType.FIFO:
            self.deque.appendleft(item)
        else:
            self.deque.append(item)


class BuyResult:
    """
    Information about a buy action.
    """

    def __init__(self, item) -> None:
        self.item = item

    def render(self, currency, tax_currency):
        return (f'bought {currency_to_string(self.item.amount, currency)} '
                f'@ {currency_to_string(self.item.price, tax_currency)}/{currency} '
                f'({currency_to_string(self.item.cost, tax_currency)})')


class FeeResult:
    """
    Information about a fee action.
    """

    def __init__(self, sell_result) -> None:
        self.sell_result = sell_result

    def render(self, currency, tax_currency):

        out = f'fee {currency_to_string(self.sell_result.amount_sold, currency)} ' \
              f'@ {currency_to_string(self.sell_result.price_sold, tax_currency)} ' \
              f'({currency_to_string(self.sell_result.revenue_sold, tax_currency)})'

        if self.sell_result.found_unaccounted():
            out += f', ' \
                   f'unaccounted {currency_to_string(self.sell_result.amount_unaccounted, currency)} ' \
                   f'@ {currency_to_string(self.sell_result.price_sold, tax_currency)} ' \
                   f'({currency_to_string(self.sell_result.revenue_unaccounted, tax_currency)})'

        return out


class SellResult:
    """
    Information about a sell action, such as price paid, initial cost, profit / loss, etc.
    """

    def __init__(self, amount_sold, price_sold, items_bought, amount_unaccounted):
        self.amount_sold = amount_sold  # the amount sold (in original currency)
        self.price_sold = price_sold  # the price for which the amount was sold (in tax currency)
        self.items_bought = items_bought  # list of buys that correspond to the amount sold (in tax currency)
        self.amount_unaccounted = amount_unaccounted  # amount without corresponding buys (in original currency)

    @property
    def amount_bought(self):
        """
        Amount that was bought in the past and corresponds to the sale in question (in original currency).
        """
        amount_bought = Decimal('0.0')
        for item in self.items_bought:
            amount_bought += item.amount
        return amount_bought

    @property
    def cost_bought(self):
        """
        The cost of the amount when it was bought in the past (in tax currency).
        """
        cost_bought = Decimal('0.0')
        for item in self.items_bought:
            cost_bought += item.cost
        return cost_bought

    @property
    def price_bought(self):
        """
        The price of the amount when it was bought in the past (in tax currency).
        """
        if self.amount_bought == Decimal('0.0'):
            return Decimal('0.0')
        return self.cost_bought / self.amount_bought

    @property
    def revenue_sold(self):
        """
        The revenue of the amount when it was sold (in tax currency). Includes unaccounted revenue.
        """
        return self.amount_sold * self.price_sold

    @property
    def revenue_unaccounted(self):
        """
        Revenue for which no cost could be determined.
        """
        return self.amount_unaccounted * self.price_sold

    @property
    def pl(self):
        """
        Profit / loss of the sale (in tax currency). This includes profit from unaccounted revenue.
        """
        return self.revenue_sold - self.cost_bought

    def found_unaccounted(self):
        """
        Returns True if a part of the amount could not be accounted for.
        """
        return self.amount_unaccounted > Decimal('0.0')

    def render(self, currency, tax_currency):

        out = f'sold {currency_to_string(self.amount_sold, currency)} ' \
              f'@ {currency_to_string(self.price_sold, tax_currency)}/{currency} ' \
              f'({currency_to_string(self.revenue_sold, tax_currency)}), ' \
              f'bought {currency_to_string(self.amount_bought, currency)} ' \
              f'@ {currency_to_string(self.price_bought, tax_currency)}/{currency} ' \
              f'({currency_to_string(self.cost_bought, tax_currency)}), '

        if self.found_unaccounted():
            out += f'unaccounted {currency_to_string(self.amount_unaccounted, currency)} ' \
                   f'@ {currency_to_string(self.price_sold, tax_currency)}/{currency} ' \
                   f'({currency_to_string(self.revenue_unaccounted, tax_currency)}), '

        out += f'P/L: {currency_to_string(self.pl, tax_currency)}'
        return out


class Item:
    """
    Represents an amount bought in the past (in original currency)
    and the price that was paid (in tax currency).
    """

    def __init__(self, amount, price):
        self.amount = amount
        self.price = price

    @property
    def cost(self):
        return self.amount * self.price
