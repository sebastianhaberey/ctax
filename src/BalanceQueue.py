from collections import deque, defaultdict
from decimal import Decimal
from enum import Enum
from functools import reduce

from src.NumberUtils import currency_to_string
from src.bo.SellInfo import SellInfo
from src.bo.Transaction import TransactionType


class QueueType(Enum):
    """
    Type of queue.
    """
    FIFO = 0
    LIFO = 1


class BalanceQueue:
    """
    Queue that keeps a tab of amounts bought, their price, and the current balance.
    When an amount is sold, its cost and buying fees are calculated by FIFO (default) or LIFO principle.
    """

    def __init__(self, queue_type, fees_are_tax_deductible):
        self.queue_type = queue_type
        self.fees_are_tax_deductible = fees_are_tax_deductible
        self.queues = defaultdict(lambda: deque())

    def get_balance(self, currency):
        """
        Returns the balance for the specified currency.
        """

        return reduce(lambda a, b: a + b.amount, self.queues[currency], Decimal(0))

    def trade(self, trade):
        """
        Simulates a trade.
        :return: a SellInfo object with information about the selling part of the trade
        """
        sell = trade.get_transaction(TransactionType.SELL)
        sell_info = self._sell(self.queues[sell.currency], trade)

        buy = trade.get_transaction(TransactionType.BUY)
        self._buy(self.queues[buy.currency], trade)

        return sell_info

    def _buy(self, queue, trade):
        self._put(queue, Item(trade.get_transaction(TransactionType.BUY).amount, trade))

    def _sell(self, queue, trade):

        remaining_sell_amount = trade.get_transaction(TransactionType.SELL).amount
        items_bought = []

        while remaining_sell_amount > Decimal('0'):

            if self._is_empty(queue):  # no bought items left but sell is not fully covered
                items_bought.append(Item(remaining_sell_amount, None))
                break

            item = self._pop(queue, self.queue_type)

            if remaining_sell_amount < item.amount:  # sell amount is entirely covered by bought items
                items_bought.append(Item(remaining_sell_amount, item.trade))
                item.amount -= remaining_sell_amount
                self._put_back(queue, self.queue_type, item)
                break
            elif remaining_sell_amount >= item.amount:  # bought item is fully consumed by sell
                items_bought.append(item)
                remaining_sell_amount -= item.amount

        return SellInfo(trade, items_bought)

    @staticmethod
    def _is_empty(queue):
        return len(queue) == 0

    @staticmethod
    def _pop(queue, queue_type):
        if queue_type == QueueType.FIFO:
            item = queue.popleft()
        else:
            item = queue.pop()
        return item

    @staticmethod
    def _put_back(queue, queue_type, item):
        if queue_type == QueueType.FIFO:
            queue.appendleft(item)
        else:
            queue.append(item)

    @staticmethod
    def _put(queue, item):
        queue.append(item)

    def __str__(self) -> str:
        amounts = []
        for currency in self.queues:
            amounts.append(currency_to_string(self.get_balance('currency'), currency))
        return f'{amounts}'


class Item:
    """
    Represents an percentage of a an amount bought in the past, and the corresponding trade.
    """

    def __init__(self, amount, trade):
        """
        :param trade: corresponding trade or None if unaccounted
        """
        self.amount = amount
        self.trade = trade

    @property
    def percent(self):
        """
        How much of the trade amount this item represents, in percent (0.0 - 1.0).
        """
        if self.trade is None:  # no trade means unaccounted
            return Decimal('1.0')  # 100 percent of unaccounted trade are relevant

        return self.amount / self.trade.get_transaction(TransactionType.BUY).amount

    @property
    def cost(self):
        """
        The cost of the item (converted to tax currency).
        """

        if self.trade is None:  # no trade means unaccounted
            return Decimal('0.0')  # unaccounted means no cost

        return self.percent * self.trade.get_transaction(TransactionType.SELL).converted_amount

    @property
    def fee(self):
        """
        The cost of the item (converted to tax currency).
        """

        if self.trade is None:  # no trade means unaccounted
            return Decimal('0.0')  # unaccounted means no fee

        return self.percent * self.trade.get_transaction(TransactionType.FEE).converted_amount
