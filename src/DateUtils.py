from dateutil.parser import parse
from dateutil.tz import tzoffset
from dateutil.utils import default_tzinfo


def parse_date(text):
    return default_tzinfo(parse(text), tzoffset("UTC", 0))


def date_to_simple_string_with_time(date):
    return date.strftime("%d.%m.%Y %H:%M:%S %Z")


def date_to_simple_string(date):
    return date.strftime("%d.%m.%Y")
