from datetime import datetime
from decimal import Decimal
from unittest import TestCase

from dateutil.tz import UTC

from src.CcxtOrderImporter import import_orders
from src.bo.Transaction import TransactionType
from test.testdata.BitfinexTrades import bitfinex_trades
from test.testdata.KrakenTrades import kraken_trades

SYMBOLS = {
    'BTC/EUR': {
        'base': 'BTC',
        'quote': 'EUR'
    },
    'ETH/USD': {
        'base': 'ETH',
        'quote': 'USD'
    },
}


class TestCcxtOrderImporter(TestCase):

    def test_import_orders_bitfinex(self):
        orders = import_orders(bitfinex_trades, 'bitfinex', datetime(2017, 1, 1, tzinfo=UTC),
                               datetime(2018, 1, 1, tzinfo=UTC), self._currency_lookup)

        self.assertEqual(1, len(orders))
        order = orders[0]

        self.assertEqual(2, len(order.trades))
        trade = order.trades[0]
        self.assertEqual('10000000', trade.source_id)
        self.assertEqual(3, len(trade.transactions))

        buy = trade.get_transaction(TransactionType.BUY)
        self.assertIsNotNone(buy)
        self.assertEqual("USD", buy.currency)
        self.assertEqual(Decimal("5.8") * Decimal("200.0"), buy.amount)

        sell = trade.get_transaction(TransactionType.SELL)
        self.assertIsNotNone(sell)
        self.assertEqual("ETH", sell.currency)
        self.assertEqual(Decimal("5.8"), sell.amount)

        fee = trade.get_transaction(TransactionType.FEE)
        self.assertIsNotNone(fee)
        self.assertEqual("EUR", fee.currency)
        self.assertEqual(Decimal("0.005"), fee.amount)

        trade = order.trades[1]
        self.assertEqual('10000001', trade.source_id)
        self.assertEqual(3, len(trade.transactions))

        buy = trade.get_transaction(TransactionType.BUY)
        self.assertIsNotNone(buy)
        self.assertEqual("ETH", buy.currency)
        self.assertEqual(Decimal("10.5"), buy.amount)

        sell = trade.get_transaction(TransactionType.SELL)
        self.assertIsNotNone(sell)
        self.assertEqual("USD", sell.currency)
        self.assertEqual(Decimal("10.5") * Decimal("220.3"), sell.amount)

        fee = trade.get_transaction(TransactionType.FEE)
        self.assertIsNotNone(fee)
        self.assertEqual("INR", fee.currency)
        self.assertEqual(Decimal("1.3"), fee.amount)

    def test_import_orders(self):
        orders = import_orders(kraken_trades, 'kraken', datetime(2017, 1, 1, tzinfo=UTC),
                               datetime(2018, 1, 1, tzinfo=UTC), self._currency_lookup)

        self.assertEqual(1, len(orders))
        order = orders[0]

        self.assertEqual(2, len(order.trades))
        trade = order.trades[0]
        self.assertEqual('ABCDEF-GHIJK-LMNOPQ', trade.source_id)
        self.assertEqual(3, len(trade.transactions))

        buy = trade.get_transaction(TransactionType.BUY)
        self.assertIsNotNone(buy)
        self.assertEqual("BTC", buy.currency)
        self.assertEqual(Decimal("0.02"), buy.amount)

        sell = trade.get_transaction(TransactionType.SELL)
        self.assertIsNotNone(sell)
        self.assertEqual("EUR", sell.currency)
        self.assertEqual(Decimal("0.02") * Decimal("1000.0"), sell.amount)

        fee = trade.get_transaction(TransactionType.FEE)
        self.assertIsNotNone(fee)
        self.assertEqual("EUR", fee.currency)
        self.assertEqual(Decimal("0.05"), fee.amount)

        trade = order.trades[1]
        self.assertEqual('AAAAAA-AAAAA-AAAAAA', trade.source_id)
        self.assertEqual(3, len(trade.transactions))

        buy = trade.get_transaction(TransactionType.BUY)
        self.assertIsNotNone(buy)
        self.assertEqual("USD", buy.currency)
        self.assertEqual(Decimal("15.3") * Decimal("150.1"), buy.amount)

        sell = trade.get_transaction(TransactionType.SELL)
        self.assertIsNotNone(sell)
        self.assertEqual("ETH", sell.currency)
        self.assertEqual(Decimal("15.3"), sell.amount)

        fee = trade.get_transaction(TransactionType.FEE)
        self.assertIsNotNone(fee)
        self.assertEqual("USD", fee.currency)
        self.assertEqual(Decimal("0.02"), fee.amount)

    @staticmethod
    def _currency_lookup(symbol, currency_type):
        return SYMBOLS[symbol][currency_type]
