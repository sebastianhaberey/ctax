from datetime import datetime
from unittest import TestCase

from dateutil.tz import UTC

from src.Configuration import Configuration

TESTDATA_CONFIGURATION = """

  tax-year: 2018

"""


class TestConfiguration(TestCase):

    def setUp(self):
        self.configuration = Configuration(TESTDATA_CONFIGURATION)

    def test_get_date_from(self):
        self.assertEqual(datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=UTC), self.configuration.get_date_from())

    def test_get_date_to(self):
        self.assertEqual(datetime(2019, 1, 1, 0, 0, 0, 0, tzinfo=UTC), self.configuration.get_date_to())
