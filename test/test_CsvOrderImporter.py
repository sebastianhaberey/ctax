from decimal import Decimal
from unittest import TestCase

from src.Configuration import Configuration
from src.CsvOrderImporter import CsvOrderImporter
from src.bo.Transaction import TransactionType

TESTDATA_CONFIGURATION_BITFINEX = """

tax-year: 2017

files:

- exchange: 'bitfinex'
  files: ['testdata/bitfinex-trades.csv']
  delimiter: ','
  quotechar: '"'
  encoding: 'utf8'
  currency-map: { }
  columns:
    id:
      name: '#'
    date:
      name: 'Date'
    base-currency:
      name: 'Pair'
      regex: '^(.*)\/.*$'
    quote-currency:
      name: 'Pair'
      regex: '^.*\/(.*)$'
    fee-currency:
      name: 'FeeCurrency'
      regex: '^(.*)$'
    base:
      name: 'Amount'
    price:
      name: 'Price'
    fee:
      name: 'Fee'
    sell-indicator:
      name: 'Amount'
      regex: '^(-).*$'

"""

TESTDATA_CONFIGURATION_KRAKEN = """

tax-year: 2017

files:

- exchange: 'kraken'
  files: ['testdata/kraken-trades.csv']
  delimiter: ','
  quotechar: '"'
  encoding: 'utf8'
  currency-map: { 'XXBT': 'BTC', 'XETH': 'ETH', 'ZUSD': 'USD', 'ZEUR': 'EUR' }
  columns:
    id:
      name: 'txid'
    date:
      name: 'time'
    base-currency:
      name: 'pair'
      regex: '^(.{4}).{4}$'
    quote-currency:
      name: 'pair'
      regex: '^.{4}(.{4})$'
    fee-currency:
      name: 'pair'
      regex: '^.{4}(.{4})$'
    base:
      name: 'vol'
    price:
      name: 'price'
    fee:
      name: 'fee'
    sell-indicator:
      name: 'type'
      regex: '^(sell)$'
      

"""


class TestCsvOrderImporter(TestCase):

    def test_import_orders_bitfinex(self):
        importer = CsvOrderImporter(Configuration(TESTDATA_CONFIGURATION_BITFINEX))

        orders = importer.import_orders()
        self.assertEqual(2, len(orders))

        order = orders[0]
        self.assertEqual(1, len(order.trades))
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

        order = orders[1]
        self.assertEqual(1, len(order.trades))
        trade = order.trades[0]
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

    def test_import_orders_kraken(self):
        importer = CsvOrderImporter(Configuration(TESTDATA_CONFIGURATION_KRAKEN))

        orders = importer.import_orders()
        self.assertEqual(2, len(orders))

        order = orders[0]
        self.assertEqual(1, len(order.trades))
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

        order = orders[1]
        self.assertEqual(1, len(order.trades))
        trade = order.trades[0]
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
