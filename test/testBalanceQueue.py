from decimal import Decimal
from unittest import TestCase

from src.BalanceQueue import BalanceQueue, QueueType


class TestBalanceQueue(TestCase):

    def test_get_balance_fresh(self):
        queue = BalanceQueue()
        self.assertEqual(Decimal('0'), queue.get_balance())

    def test_buy(self):
        queue = BalanceQueue()
        queue.buy(Decimal('1.0'), Decimal('100.0'))
        queue.buy(Decimal('2.0'), Decimal('150.0'))
        self.assertEqual(Decimal('3.0'), queue.get_balance())

    def test_buy_nothing(self):
        queue = BalanceQueue()
        queue.buy(Decimal('0.0'), Decimal('150.0'))
        self.assertEqual(Decimal('0.0'), queue.get_balance())

    def test_buy_for_free(self):
        queue = BalanceQueue()
        queue.buy(Decimal('1.0'), Decimal('0.0'))
        self.assertEqual(Decimal('1.0'), queue.get_balance())

    def test_sell(self):
        queue = BalanceQueue()
        queue.buy(Decimal('1.0'), Decimal('100.0'))
        result = queue.sell(Decimal('0.5'), Decimal('140.0'))
        self.assertEqual(Decimal('0.5'), result.amount_bought)
        self.assertEqual(Decimal('140.0'), result.price_sold)
        self.assertEqual(Decimal('50.0'), result.cost_bought)
        self.assertEqual(Decimal('70.0'), result.revenue_sold)
        self.assertEqual(Decimal('0.0'), result.amount_unaccounted)
        self.assertEqual(Decimal('0.0'), result.revenue_unaccounted)
        self.assertEqual(Decimal('20.0'), result.pl)
        self.assertEqual(Decimal('0.5'), queue.get_balance())

    def test_sell_with_unaccounted(self):
        queue = BalanceQueue()
        queue.buy(Decimal('1.0'), Decimal('100.0'))
        result = queue.sell(Decimal('1.5'), Decimal('240.0'))
        self.assertEqual(Decimal('1.0'), result.amount_bought)
        self.assertEqual(Decimal('240.0'), result.price_sold)
        self.assertEqual(Decimal('100.0'), result.cost_bought)
        self.assertEqual(Decimal('360.0'), result.revenue_sold)
        self.assertEqual(Decimal('0.5'), result.amount_unaccounted)
        self.assertEqual(Decimal('120.0'), result.revenue_unaccounted)
        self.assertEqual(Decimal('260.0'), result.pl)
        self.assertEqual(Decimal('0.0'), queue.get_balance())

    def test_sell_with_loss_and_unaccounted(self):
        queue = BalanceQueue()
        queue.buy(Decimal('1.0'), Decimal('200.0'))
        result = queue.sell(Decimal('2'), Decimal('80.0'))
        self.assertEqual(Decimal('1.0'), result.amount_bought)
        self.assertEqual(Decimal('80.0'), result.price_sold)
        self.assertEqual(Decimal('200.0'), result.cost_bought)
        self.assertEqual(Decimal('160.0'), result.revenue_sold)
        self.assertEqual(Decimal('1.0'), result.amount_unaccounted)
        self.assertEqual(Decimal('80.0'), result.revenue_unaccounted)
        self.assertEqual(Decimal('-40.0'), result.pl)
        self.assertEqual(Decimal('0.0'), queue.get_balance())


    def test_sell_empty_queue(self):
        queue = BalanceQueue()
        result = queue.sell(Decimal('1.0'), Decimal('120.0'))
        self.assertEqual(Decimal('0.0'), result.amount_bought)
        self.assertEqual(Decimal('120.0'), result.price_sold)
        self.assertEqual(Decimal('0.0'), result.cost_bought)
        self.assertEqual(Decimal('120.0'), result.revenue_sold)
        self.assertEqual(Decimal('1.0'), result.amount_unaccounted)
        self.assertEqual(Decimal('120.0'), result.revenue_unaccounted)
        self.assertEqual(Decimal('120.0'), result.pl)
        self.assertEqual(Decimal('0.0'), queue.get_balance())

    def test_sell_nothing_empty_queue(self):
        queue = BalanceQueue()
        result = queue.sell(Decimal('0.0'), Decimal('0.0'))
        self.assertEqual(Decimal('0.0'), result.amount_bought)
        self.assertEqual(Decimal('0.0'), result.price_sold)
        self.assertEqual(Decimal('0.0'), result.cost_bought)
        self.assertEqual(Decimal('0.0'), result.revenue_sold)
        self.assertEqual(Decimal('0.0'), result.amount_unaccounted)
        self.assertEqual(Decimal('0.0'), result.revenue_unaccounted)
        self.assertEqual(Decimal('0.0'), result.pl)
        self.assertEqual(Decimal('0.0'), queue.get_balance())

    def test_fifo(self):
        queue = BalanceQueue(QueueType.FIFO)
        queue.buy(Decimal('1.0'), Decimal('100.0'))
        queue.buy(Decimal('1.0'), Decimal('10.0'))
        result = queue.sell(Decimal('1.5'), Decimal('200.0'))
        self.assertEqual(Decimal('1.5'), result.amount_bought)
        self.assertEqual(Decimal('105.0'), result.cost_bought)

    def test_lifo(self):
        queue = BalanceQueue(QueueType.LIFO)
        queue.buy(Decimal('1.0'), Decimal('100.0'))
        queue.buy(Decimal('1.0'), Decimal('10.0'))
        result = queue.sell(Decimal('1.5'), Decimal('200.0'))
        self.assertEqual(Decimal('1.5'), result.amount_bought)
        self.assertEqual(Decimal('60.0'), result.cost_bought)
