import os
from datetime import datetime
from unittest import TestCase

from dateutil.tz import UTC

from src.Configuration import Configuration
from src.Error import Error

TESTDATA_CONFIGURATION_FILE = os.path.join(os.path.dirname(__file__), 'testdata', 'configuration.yml')
TESTDATA_CONFIGURATION_FILE_NOT_FOUND = os.path.join(os.path.dirname(__file__), 'foo')

TESTDATA_CONFIGURATION_TEXT = """

  tax-year: 2018
  some-value: True

"""


class TestConfiguration(TestCase):

    def test_from_file(self):
        configuration = Configuration.from_file(TESTDATA_CONFIGURATION_FILE)
        self.assertEqual(configuration.get('month'), 'August')

    def test_file_not_found(self):
        with self.assertRaises(Error) as context:
            Configuration.from_file(TESTDATA_CONFIGURATION_FILE_NOT_FOUND)
        self.assertRegex(str(context.exception), 'file not found')

    def test_error_parsing(self):
        with self.assertRaises(Error) as context:
            Configuration.from_string("'")
        self.assertRegex(str(context.exception), 'error parsing')

    def test_key_invalid(self):
        configuration = Configuration.from_string(TESTDATA_CONFIGURATION_TEXT)
        with self.assertRaises(Error) as context:
            configuration.get(5)
        self.assertRegex(str(context.exception), 'invalid configuration key')

    def test_get_not_found(self):
        configuration = Configuration.from_string(TESTDATA_CONFIGURATION_TEXT)
        self.assertEqual(None, configuration.get('nonexisting'))

    def test_get_mandatory_not_found(self):
        configuration = Configuration.from_string(TESTDATA_CONFIGURATION_TEXT)
        with self.assertRaises(Error) as context:
            configuration.get_mandatory('nonexisting')
        self.assertRegex(str(context.exception), 'mandatory configuration item not found')

    def test_is_true(self):
        configuration = Configuration.from_string(TESTDATA_CONFIGURATION_TEXT)
        self.assertTrue(configuration.is_true('some-value'))

    def test_exists(self):
        configuration = Configuration.from_string(TESTDATA_CONFIGURATION_TEXT)
        self.assertTrue(configuration.is_true('some-value'))

    def test_get_date_from(self):
        configuration = Configuration.from_string(TESTDATA_CONFIGURATION_TEXT)
        self.assertEqual(datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=UTC), configuration.get_date_from())

    def test_get_date_to(self):
        configuration = Configuration.from_string(TESTDATA_CONFIGURATION_TEXT)
        self.assertEqual(datetime(2019, 1, 1, 0, 0, 0, 0, tzinfo=UTC), configuration.get_date_to())
