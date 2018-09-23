from datetime import datetime
from unittest import TestCase

from dateutil.tz import UTC

from src.bo.Order import Order, sort_orders_by_time
from src.bo.Trade import Trade


class TestOrder(TestCase):

    def test_sort_orders_by_time(self):
        order_a = Order(None, None)
        trade_a = Trade(None, datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=UTC), None)
        # false positive (apparently PyCharm does not recognize the ORM relationship collection correctly)
        # noinspection PyUnresolvedReferences
        order_a.trades.append(trade_a)

        order_b = Order(None, None)
        trade_b = Trade(None, datetime(2018, 1, 1, 0, 0, 0, 1, tzinfo=UTC), None)
        # false positive (apparently PyCharm does not recognize the ORM relationship collection correctly)
        # noinspection PyUnresolvedReferences
        order_b.trades.append(trade_b)

        order_c = Order(None, None)
        trade_c = Trade(None, datetime(2018, 1, 1, 0, 0, 0, 2, tzinfo=UTC), None)
        # false positive (apparently PyCharm does not recognize the ORM relationship collection correctly)
        # noinspection PyUnresolvedReferences
        order_c.trades.append(trade_c)

        self.assertListEqual(sort_orders_by_time([order_c, order_b, order_a]), [order_a, order_b, order_c])
        self.assertListEqual(sort_orders_by_time([order_b, order_a, order_c]), [order_a, order_b, order_c])
