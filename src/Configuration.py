from datetime import datetime

import yaml
from dateutil.tz import UTC

from src.DateUtils import parse_date


class ConfigurationError(Exception):
    """
    Signals an error while accessing the configuration.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)


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
        except FileNotFoundError as exc:
            raise ConfigurationError(f'configuration file not found: {file_name}') from None

    @classmethod
    def from_string(cls, text):
        return cls(text)

    def __init__(self, stream):
        try:
            self.configuration = yaml.load(stream)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f'invalid configuration format in file {file_name}: {exc.msg}') from None

    def __getitem__(self, key):
        return self.configuration[key]

    def __setitem__(self, key, value):
        self.configuration[value] = value

    def get(self, *keys, default=None):
        """
        Looks for a value in the configuration tree by its keys and returns it, or a default value if not found.
        Example: get('logging', 'loglevel', default='INFO')
        """
        value = self.configuration
        for key in keys:
            if not isinstance(key, str):
                raise ConfigurationError(f'illegal configuration key: {keys}')
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
            raise ConfigurationError(f'mandatory configuration item not found: {".".join(args)}')
        return value

    def is_true(self, *args, default=False):
        """
        Checks if a boolean value in the configuration tree is true.
        """
        return self.get(*args, default=default) is True

    def exists(self, *args):
        """
        Checks if a boolean value in the configuration tree exists and is not empty.
        """
        return self.get(*args, default=None) is not None

    def get_date(self, *args, default=None):
        """
        Returns the specified date from the configuration.
        Must be in ISO8601 format (example: 2017-01-01T00:00:00.000Z).
        """
        value = self.get(*args, default=None)
        if value is None:
            return default
        return parse_date(value)

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
