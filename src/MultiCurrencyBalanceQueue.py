from collections import defaultdict
from decimal import Decimal

from src.BalanceQueue import BalanceQueue, QueueType
from src.NumberUtils import currency_to_string


class MultiCurrencyBalanceQueue:

    def __init__(self, tax_currency, queue_type=QueueType.FIFO):
        self.tax_currency = tax_currency
        self.queues = defaultdict(lambda: BalanceQueue(queue_type))
        self.queues[tax_currency].buy(Decimal('100000'), Decimal('1.0'))

    def buy(self, group):
        return self.queues[group.currency].buy(group.amount, group.exchange_rate)

    def sell(self, group):
        return self.queues[group.currency].sell(group.amount, group.exchange_rate)

    def fee(self, group):
        return self.queues[group.currency].fee(group.amount, group.exchange_rate)

    def get_balance(self, currency):
        return self.queues[currency].get_balance()

    def __str__(self) -> str:
        amounts = []
        for currency in self.queues:
            amounts.append(currency_to_string(self.queues[currency].get_balance(), currency))
        return f'{amounts}'
