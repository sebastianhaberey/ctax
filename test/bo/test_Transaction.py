import unittest
from decimal import Decimal

from src.bo.Transaction import Transaction, TransactionType


def create_transaction(id):
    transaction = Transaction()
    transaction.id = id
    transaction.trade_id = 10
    transaction.amount = '10.5'
    transaction.type = TransactionType.FEE
    transaction.currency = 'EUR'
    return transaction


class TestTransaction(unittest.TestCase):

    def test_id_equal_but_not_equal(self):
        a = create_transaction(1)
        a.currency = 'foo'

        b = create_transaction(1)
        b.currency = 'bar'

        self.assertNotEqual(a, b)

    def test_id_not_equal_but_equal(self):
        a = create_transaction(1)
        b = create_transaction(2)

        self.assertEqual(a, b)

    def test_trade_id_not_equal_but_equal(self):
        a = create_transaction(1)
        a.trade_id = 10

        b = create_transaction(1)
        b.trade_id = 20

        self.assertEqual(a, b)

    def test_id_not_set_but_equal(self):
        a = create_transaction(1)
        b = create_transaction(None)

        self.assertEqual(a, b)

    def test_set_difference(self):
        set_a = {(create_transaction(1))}
        set_b = {(create_transaction(2))}

        self.assertEqual(0, len(set_a - set_b))

    def test_amount(self):
        a = Transaction()
        a.amount = '10.5'
        self.assertEqual(Decimal('10.5'), a.amount)

    def test_amount_none(self):
        a = Transaction()
        a.amount = None
        self.assertEqual(None, a.amount)

    def test_str(self):
        transaction = create_transaction(1)
        self.assertEqual('id: 1, type: FEE, amount: 10.50 EUR', transaction.__str__())

    def test_equal(self):
        a = create_transaction(1)
        a.trade_id = 10
        b = create_transaction(2)
        b.trade_id = 20

        self.assertEqual(a, b)


if __name__ == '__main__':
    unittest.main()
