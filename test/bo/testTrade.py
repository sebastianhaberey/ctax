import datetime
from unittest import TestCase

from src.bo.Trade import Trade, Error
from src.bo.Transaction import Transaction, TransactionType


class TestTrade(TestCase):

    def test_get_transaction(self):
        buy = Transaction()
        buy.type = TransactionType.BUY

        sell = Transaction()
        sell.type = TransactionType.SELL

        fee = Transaction()
        fee.type = TransactionType.FEE

        trade = Trade('foo', datetime.datetime.now(), (sell, buy, fee))

        self.assertEqual(trade.get_transaction(TransactionType.BUY), buy)
        self.assertEqual(trade.get_transaction(TransactionType.SELL), sell)
        self.assertEqual(trade.get_transaction(TransactionType.FEE), fee)

    def test_get_transaction_double(self):
        buy1 = Transaction()
        buy1.type = TransactionType.BUY

        buy2 = Transaction()
        buy2.type = TransactionType.BUY

        trade = Trade('foo', datetime.datetime.now(), (buy1, buy2))

        self.assertRaises(Error, trade.get_transaction, TransactionType.BUY)

    def test_get_transaction_none(self):
        trade = Trade('foo', datetime.datetime.now(), ())
        self.assertRaises(Error, trade.get_transaction, TransactionType.BUY)
