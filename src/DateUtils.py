from datetime import datetime

from dateutil.parser import parse
from dateutil.tz import tzoffset, UTC
from dateutil.utils import default_tzinfo


def parse_date(text):
    return default_tzinfo(parse(text), tzoffset("UTC", 0))


def date_to_string(date):
    return date.strftime("%d.%m.%Y")


def date_and_time_to_string(date):
    return date.strftime("%d.%m.%Y %H:%M:%S %Z")


def get_start_of_year(year):
    """
    Returns start of year.
    """

    return datetime(year, 1, 1, tzinfo=UTC)


def get_start_of_year_after(year):
    """
    Returns first instant of next year.
    """

    return datetime(year + 1, 1, 1, tzinfo=UTC)
