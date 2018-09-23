from datetime import datetime
from unittest import TestCase

from dateutil.tz import UTC

from src.DateUtils import get_start_of_year, get_start_of_year_after, date_to_string, date_and_time_to_string


class TestDateUtils(TestCase):

    def test_get_start_of_year(self):
        self.assertEqual(datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=UTC), get_start_of_year(2018))

    def test_get_start_of_year_after(self):
        self.assertEqual(datetime(2019, 1, 1, 0, 0, 0, 0, tzinfo=UTC), get_start_of_year_after(2018))

    def test_date_to_string(self):
        self.assertEqual("01.01.2018", date_to_string(datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=UTC)))

    def test_date_and_time_to_string(self):
        self.assertEqual("01.01.2018 00:00:00 UTC",
                         date_and_time_to_string(datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=UTC)))
