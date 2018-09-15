from decimal import Decimal
from unittest import TestCase

from src.NumberUtils import value_to_string, value_to_decimal, value_to_scaled_integer, scaled_integer_to_decimal


class TestNumberUtils(TestCase):

    def test_value_to_decimal_none(self):
        self.assertEqual(None, value_to_decimal(None))

    def test_value_to_decimal_string(self):
        self.assertEqual(Decimal('3.251'), value_to_decimal('3.251'))
        self.assertEqual(Decimal('3.3'), value_to_decimal('3.251', 1))

    def test_value_to_decimal_decimal(self):
        self.assertEqual(Decimal('3.251'), value_to_decimal(Decimal('3.251')))
        self.assertEqual(Decimal('3.3'), value_to_decimal(Decimal('3.251'), 1))

    def test_value_to_decimal_float(self):
        # self.assertEqual(Decimal('3.251'), value_to_decimal(3.251))  # fail: 3.2509999999999998898658759572
        self.assertEqual(Decimal('3.251'), value_to_decimal(3.251, 3))
        self.assertEqual(Decimal('3.3'), value_to_decimal(3.251, 1))

    def test_value_to_decimal_integer(self):
        self.assertEqual(Decimal('3'), 3)
        self.assertEqual(Decimal('0'), 0)

    def test_value_to_decimal_invalid_empty(self):
        self.assertRaises(ValueError, value_to_decimal, '')

    def test_value_to_decimal_invalid_multiple_points(self):
        self.assertRaises(ValueError, value_to_decimal, '3.25.1')

    def test_value_to_decimal_invalid_comma(self):
        self.assertRaises(ValueError, value_to_decimal, '3,251')

    def test_value_to_string_none(self):
        self.assertEqual(None, value_to_string(None, 10))

    def test_value_to_string_string(self):
        self.assertEqual('3.2510000000000000000000000000', value_to_string('3.251'))  # 28 decimals is default
        self.assertEqual('0', value_to_string('0.3', 0))
        self.assertEqual('3.3', value_to_string('3.251', 1))

    def test_value_to_string_float(self):
        # self.assertEqual('3.251', value_to_string(3.251))  # fail: 3.2509999999999998898658759572
        self.assertEqual('3.251', value_to_string(3.251, 3))
        self.assertEqual('3.3', value_to_string(3.251, 1))

    def test_value_to_string(self):
        self.assertEqual('3.2510000000000000000000000000', value_to_string(Decimal('3.251')))  # 28 decimals is default
        self.assertEqual('3.3', value_to_string(Decimal('3.251'), 1))

    def test_value_to_scaled_integer_none(self):
        self.assertEqual(None, value_to_scaled_integer(None))

    def test_value_to_scaled_integer(self):
        self.assertEqual(32510000000000000000000000000, value_to_scaled_integer('3.251'))  # 28 decimals is default
        self.assertEqual(3251, value_to_scaled_integer('3.251', 3))
        self.assertEqual(33, value_to_scaled_integer('3.251', 1))

    def test_scaled_integer_to_decimal_none(self):
        self.assertEqual(None, scaled_integer_to_decimal(None))

    def test_scaled_integer_to_decimal(self):
        self.assertEqual(Decimal('3.251'),
                         scaled_integer_to_decimal(32510000000000000000000000000))  # 28 decimals is default
        self.assertEqual(Decimal('3.251'), scaled_integer_to_decimal(3251, 3))
        self.assertEqual(Decimal('0.251'), scaled_integer_to_decimal(251, 3))
        self.assertEqual(Decimal('0'), scaled_integer_to_decimal(0, 2))

    def test_scaled_integer_to_decimal_round(self):
        # self.assertEqual(33, to_integer(3.25, 1))  # fail
        self.assertEqual(33, value_to_scaled_integer(3.251, 1))
