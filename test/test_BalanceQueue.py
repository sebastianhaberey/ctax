from decimal import Decimal
from unittest import TestCase

from src.BalanceQueue import BalanceQueue, QueueType
from test.utilities.TradeCreator import TradeCreator

TAX_CURRENCY = 'EUR'

DEFAULT_EXCHANGE_RATES = {
    'BTC': '1000.0',
    'USD': '1.5',
    'ETH': '100.0',
}


class TestBalanceQueue(TestCase):

    def setUp(self):
        self.trade_creator = TradeCreator(TAX_CURRENCY, DEFAULT_EXCHANGE_RATES)
        self.queue = BalanceQueue(QueueType.FIFO, True)

    def test_balances_fresh(self):
        """
        Asserts correct balances after initialization.
        """

        self.assertEqual(Decimal('0'), self.queue.get_balance('EUR'))
        self.assertEqual(Decimal('0'), self.queue.get_balance('USD'))
        self.assertEqual(Decimal('0'), self.queue.get_balance('ETH'))
        self.assertEqual(Decimal('0'), self.queue.get_balance('BTC'))

    def test_balances(self):
        """
        Asserts correct balances after a trade.
        Asserts that balances do not go negative.
        Assert that fees do not count towards balances.
        """

        # buy BTC for EUR @ 1000
        self.queue.trade(self.trade_creator.create_trade({
            'sell': ['EUR', '1000'],
            'buy': ['BTC', '1'],
            'fee': ['BTC', '0.001']
        }))

        self.assertEqual(Decimal('0'), self.queue.get_balance('EUR'), 'queue balance does not go negative')
        self.assertEqual(Decimal('1'), self.queue.get_balance('BTC'))

    def test_trade_empty_queue(self):
        """
        Asserts correct info when trading on empty queue.
        Asserts that all unaccounted sell actions are treated as 100% profit.
        """

        # buy ETH for BTC @ 10
        info = self.queue.trade(self.trade_creator.create_trade({
            'sell': ['BTC', '1'],
            'buy': ['ETH', '10'],
            'fee': ['ETH', '0.1']
        }))

        self.assertEqual(Decimal('1'), info.amount, 'amount sold 1 BTC')
        self.assertEqual(Decimal('1000'), info.proceeds, 'proceeds 1000 EUR')
        self.assertEqual(Decimal('10'), info.selling_fees, 'selling fees 10 EUR')
        self.assertEqual(Decimal('0'), info.cost, 'cost 0 (unaccounted)')
        self.assertEqual(Decimal('0'), info.buying_fees, 'buying fees 0 (unaccounted)')
        self.assertEqual(Decimal('990'), info.pl, 'profit 990 EUR')

        self.assertEqual(Decimal('10'), self.queue.get_balance('ETH'))
        self.assertEqual(Decimal('0'), self.queue.get_balance('BTC'))

    def test_trade_fiat_crypto_fiat_no_price_change(self):
        """
        Asserts correct info when buying crypto for fiat and selling a portion of it again (for fiat)
        without any change in exchange rates in between.
        """

        # buy BTC for EUR @ 1000
        self.queue.trade(self.trade_creator.create_trade({
            'sell': ['EUR', '1000.0'],
            'buy': ['BTC', '1.0'],
            'fee': ['BTC', '0.01']
        }))

        # sell BTC for EUR @ 1000
        info = self.queue.trade(self.trade_creator.create_trade({
            'sell': ['BTC', '0.7'],
            'buy': ['EUR', '700.0'],
            'fee': ['EUR', '7.0']
        }))

        self.assertEqual(Decimal('0.7'), info.amount, 'amount sold 0.7 BTC')
        self.assertEqual(Decimal('700'), info.proceeds, 'proceeds 700 EUR')
        self.assertEqual(Decimal('7'), info.selling_fees, 'selling fees 7 EUR')
        self.assertEqual(Decimal('700'), info.cost, 'cost 700 EUR')
        self.assertEqual(Decimal('7'), info.buying_fees, 'buying fees 7 EUR')
        self.assertEqual(Decimal('-14'), info.pl, 'bought for 700 EUR + 7 EUR and sold for 700 EUR - 7 EUR')

        self.assertEqual(Decimal('700'), self.queue.get_balance('EUR'))
        self.assertEqual(Decimal('0.3'), self.queue.get_balance('BTC'))

    def test_trade_fiat_crypto_fiat_price_up(self):
        """
        Asserts correct info when buying crypto for fiat and selling a portion of it again (for fiat)
        while the price of the crypto currency has doubled.
        """

        # buy BTC for EUR @ 1000
        self.queue.trade(self.trade_creator.create_trade({
            'sell': ['EUR', '1000'],
            'buy': ['BTC', '1'],
            'fee': ['BTC', '0.01']
        }))

        self.trade_creator.set_tax_exchange_rate('BTC', '2000')

        # sell BTC for EUR @ 2000
        info = self.queue.trade(self.trade_creator.create_trade({
            'sell': ['BTC', '0.7'],
            'buy': ['EUR', '1400'],
            'fee': ['EUR', '14']
        }))

        self.assertEqual(Decimal('0.7'), info.amount, 'amount sold 0.7 BTC')
        self.assertEqual(Decimal('1400'), info.proceeds, 'proceeds 1400 EUR')
        self.assertEqual(Decimal('14'), info.selling_fees, 'selling fees 14 EUR')
        self.assertEqual(Decimal('700'), info.cost, 'cost 700 EUR')
        self.assertEqual(Decimal('7'), info.buying_fees, 'buying fees 7 EUR')
        self.assertEqual(Decimal('679'), info.pl, 'bought for 700 EUR + 7 EUR and sold for 1400 EUR - 14 EUR')

        self.assertEqual(Decimal('1400'), self.queue.get_balance('EUR'))
        self.assertEqual(Decimal('0.3'), self.queue.get_balance('BTC'))

    def test_trade_fiat_crypto_fiat_price_down(self):
        """
        Asserts correct info when buying crypto for fiat and selling a portion of it again (for fiat)
        while the price of the crypto currency has halved.
        """

        # buy BTC for EUR @ 1000
        self.queue.trade(self.trade_creator.create_trade({
            'sell': ['EUR', '1000'],
            'buy': ['BTC', '1'],
            'fee': ['BTC', '0.01']
        }))

        self.trade_creator.set_tax_exchange_rate('BTC', '500')

        # sell BTC for EUR @ 500
        info = self.queue.trade(self.trade_creator.create_trade({
            'sell': ['BTC', '0.7'],
            'buy': ['EUR', '350'],
            'fee': ['EUR', '3.5']
        }))

        self.assertEqual(Decimal('0.7'), info.amount, 'amount sold 0.7 BTC')
        self.assertEqual(Decimal('350'), info.proceeds, 'proceeds 1400 EUR')
        self.assertEqual(Decimal('3.5'), info.selling_fees, 'selling fees 3.5 EUR')
        self.assertEqual(Decimal('700'), info.cost, 'cost 700 EUR')
        self.assertEqual(Decimal('7'), info.buying_fees, 'buying fees 7 EUR')
        self.assertEqual(Decimal('-360.5'), info.pl, 'bought for 700 EUR + 7 EUR and sold for 350 EUR - 3.5 EUR')

        self.assertEqual(Decimal('350'), self.queue.get_balance('EUR'))
        self.assertEqual(Decimal('0.3'), self.queue.get_balance('BTC'))

    def test_trade_crypto_crypto_fiat_no_price_change(self):
        """
        Asserts correct info when buying crypto for crypto.
        """

        # buy BTC for EUR @ 1000
        self.queue.trade(self.trade_creator.create_trade({
            'sell': ['EUR', '1000'],
            'buy': ['BTC', '1'],
            'fee': ['BTC', '0.01']
        }))

        # buy ETH for BTC @ 10
        info = self.queue.trade(self.trade_creator.create_trade({
            'sell': ['BTC', '0.7'],
            'buy': ['ETH', '7'],
            'fee': ['ETH', '0.07']
        }))

        self.assertEqual(Decimal('0.7'), info.amount, 'amount sold 0.7 BTC')
        self.assertEqual(Decimal('700'), info.proceeds, 'proceeds 7 ETH = 700 EUR')
        self.assertEqual(Decimal('7'), info.selling_fees, 'selling fees 0.07 ETH = 7 EUR')
        self.assertEqual(Decimal('700'), info.cost, 'cost 700 EUR')
        self.assertEqual(Decimal('7'), info.buying_fees, 'buying fees 7 EUR')
        self.assertEqual(Decimal('-14'), info.pl, 'bought for 700 EUR + 7 EUR and sold for 700 EUR - 7 EUR')

        self.assertEqual(Decimal('7'), self.queue.get_balance('ETH'))
        self.assertEqual(Decimal('0.3'), self.queue.get_balance('BTC'))

    def test_trade_fiat_crypto_fiat_sell_corresponds_to_multiple_buys(self):
        """
        Asserts correct info when buying crypto for fiat and selling a portion of it again (for fiat)
        without any change in exchange rates in between.
        """

        # buy BTC for EUR @ 500
        self.trade_creator.set_tax_exchange_rate('BTC', '500')
        self.queue.trade(self.trade_creator.create_trade({
            'sell': ['EUR', '250.0'],
            'buy': ['BTC', '0.5'],
            'fee': ['BTC', '0.005']
        }))

        # buy BTC for EUR @ 1000
        self.trade_creator.set_tax_exchange_rate('BTC', '1000')
        self.queue.trade(self.trade_creator.create_trade({
            'sell': ['EUR', '500.0'],
            'buy': ['BTC', '0.5'],
            'fee': ['BTC', '0.005']
        }))

        # sell BTC for EUR @ 1000
        info = self.queue.trade(self.trade_creator.create_trade({
            'sell': ['BTC', '0.7'],
            'buy': ['EUR', '700.0'],
            'fee': ['EUR', '7.0']
        }))

        self.assertEqual(Decimal('0.7'), info.amount, 'amount sold 0.7 BTC')
        self.assertEqual(Decimal('700'), info.proceeds, 'proceeds 700 EUR')
        self.assertEqual(Decimal('7'), info.selling_fees, 'selling fees 7 EUR')
        self.assertEqual(Decimal('450'), info.cost, 'cost '
                                                    '0.5 of 0.5 / 100% of 250 EUR (first FIFO entry) = 250 EUR '
                                                    '0.2 of 0.5 / 40% of 500 EUR (second FIFO entry) = 200 EUR')
        self.assertEqual(Decimal('4.5'), info.buying_fees, 'buying fees 4.5 EUR')
        self.assertEqual(Decimal('238.5'), info.pl, 'bought for 450 EUR + 4.5 EUR and sold for 700 EUR - 7 EUR')

        self.assertEqual(Decimal('700'), self.queue.get_balance('EUR'))
        self.assertEqual(Decimal('0.3'), self.queue.get_balance('BTC'))
