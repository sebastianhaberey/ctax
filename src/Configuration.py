from datetime import datetime

import yaml
from dateutil.tz import UTC

from src.Error import Error


class Configuration:
    """
    Encapsulates configuration file and provides various convenience methods.
    """

    @classmethod
    def from_file(cls, file_name):
        try:
            stream = open(file_name, 'r')
            obj = cls(stream)
            stream.close()
            return obj
        except FileNotFoundError:
            raise Error(f'configuration file not found: {file_name}') from None

    @classmethod
    def from_string(cls, text):
        return cls(text)

    def __init__(self, stream):
        try:
            self.configuration = yaml.load(stream)
        except yaml.YAMLError:
            raise Error(f'error parsing configuration: {stream}') from None

    def get(self, *keys, default=None):
        """
        Looks for a value in the configuration tree by its keys and returns it, or a default value if not found.
        Example: get('logging', 'loglevel', default='INFO')
        """
        value = self.configuration
        for key in keys:
            if not isinstance(key, str):
                raise Error(f'invalid configuration key: {key} (key must be string)')
            if key in value:
                value = value[key]
            else:
                return default

        return value

    def get_mandatory(self, *args):
        """
        Looks for a value in the configuration tree by its keys and returns it.
        :raises: ConfigurationError if value was not found
        """

        value = self.get(*args, default=None)
        if value is None:
            raise Error(f'mandatory configuration item not found: {".".join(args)}')
        return value

    def is_true(self, *args, default=False):
        """
        Checks if a boolean value in the configuration tree is true.
        """
        return self.get(*args, default=default) is True

    def get_date_from(self):
        """
        Returns the start of the configured tax year.
        """

        tax_year = self.get_mandatory('tax-year')
        return datetime(tax_year, 1, 1, tzinfo=UTC)

    def get_date_to(self):
        """
        Returns the start of the year after the configured tax year.
        """

        tax_year = self.get_mandatory('tax-year')
        return datetime(tax_year + 1, 1, 1, tzinfo=UTC)
