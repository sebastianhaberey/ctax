from datetime import datetime
from unittest import TestCase

from dateutil.tz import UTC

from src.bo.Trade import Trade, Error, get_earliest_trade
from src.bo.Transaction import Transaction, TransactionType


class TestTrade(TestCase):

    def test_eq(self):

        buy = Transaction()
        buy.type = TransactionType.BUY

        sell = Transaction()
        sell.type = TransactionType.SELL

        fee = Transaction()
        fee.type = TransactionType.FEE

        some_time = datetime(2000, 1, 1, tzinfo=UTC)

        trade_a = Trade('foo', some_time, (sell, buy, fee))
        trade_b = Trade('foo', some_time, (sell, buy, fee))

        self.assertEqual(trade_a, trade_b)

    def test_get_transaction(self):
        buy = Transaction()
        buy.type = TransactionType.BUY

        sell = Transaction()
        sell.type = TransactionType.SELL

        fee = Transaction()
        fee.type = TransactionType.FEE

        trade = Trade('foo', datetime.now(), (sell, buy, fee))

        self.assertEqual(trade.get_transaction(TransactionType.BUY), buy)
        self.assertEqual(trade.get_transaction(TransactionType.SELL), sell)
        self.assertEqual(trade.get_transaction(TransactionType.FEE), fee)

    def test_get_transaction_double(self):
        buy1 = Transaction()
        buy1.type = TransactionType.BUY

        buy2 = Transaction()
        buy2.type = TransactionType.BUY

        trade = Trade('foo', datetime.now(), (buy1, buy2))

        self.assertRaises(Error, trade.get_transaction, TransactionType.BUY)

    def test_get_transaction_none(self):
        trade = Trade('foo', datetime.now(), ())
        self.assertRaises(Error, trade.get_transaction, TransactionType.BUY)

    def test_get_earliest_trade(self):
        time_a = datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=UTC)
        trade_a = Trade(None, time_a, None)

        time_b = datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=UTC)
        trade_b = Trade(None, time_b, None)

        earliest_trade = get_earliest_trade([trade_a, trade_b])
        self.assertEqual(earliest_trade, trade_a)
        self.assertEqual(get_earliest_trade([trade_b, trade_a]), trade_a)
