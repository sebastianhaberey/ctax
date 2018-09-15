import csv
import re

from src.Error import Error


class column_reader:
    """
    Returns an iterable reader for the specified file.
    :param: section configuration section with information about the file such as delimiter, column infos, etc.
    """

    def __init__(self, configuration, filename):
        self._filename = filename
        self._configuration = configuration
        self._file = None

    def __enter__(self):

        delimiter = self._get_value('delimiter')
        encoding = self._get_value('encoding')
        quotechar = self._get_value('quotechar')
        columns = self._get_value('columns')
        currency_map = self._get_value('currency-map')

        self._file = open(self._filename, 'rt', encoding=encoding)
        return ColumnReader(csv.reader(self._file, delimiter=delimiter, quotechar=quotechar), columns,
                            currency_map)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()

    def _get_value(self, value_id):
        if value_id not in self._configuration:
            if 'exchange' not in self._configuration:
                raise Error(f'missing configuration value "{value_id}"')
            else:
                raise Error(f'missing configuration value "{value_id}" for exchange {self._configuration["exchange"]}')

        return self._configuration[value_id]


class ColumnReader:
    """
    Reader that iterates through rows of a CSV file and can be queried for column values.
    """

    def __init__(self, reader, columns, currency_map):
        self._reader = reader
        self._columns = columns
        self._currency_map = currency_map
        self._header = reader.__next__()
        self._row = None

    def __next__(self):
        self._row = self._reader.__next__()
        return self

    def __iter__(self):
        return self

    def get_currency(self, column_id):
        return self._map_currency(self.get(column_id))

    def _map_currency(self, currency):
        if currency in self._currency_map:
            mapped_currency = self._currency_map[currency]
            if not mapped_currency:
                raise Error(f'empty currency symbol after mapping: {currency}')
            return mapped_currency
        return currency

    def get(self, column_id, empty_allowed=False):
        """
        Returns the value of the CSV file column that is configured for the specified column id.
        If the configuration contains a regular expression for the column, the value is matched against
        the regular expression and the first match group is returned.
        """

        if column_id not in self._columns:
            raise Error(f'missing column configuration: {column_id}')

        column_properties = self._columns[column_id]

        if 'name' not in column_properties:
            raise Error(f'missing csv column name for column: {column_id}')

        csv_column_name = column_properties['name']

        if 'regex' in column_properties:
            csv_column_regex = column_properties['regex']
            value = self._get_value_with_regex(csv_column_name, csv_column_regex)
        else:
            value = self._get_value(csv_column_name)

        if not empty_allowed and not value:
            raise Error(f'column data is emtpy: {column_id}')

        return value

    def _get_value(self, csv_column_name):
        try:
            index = self._header.index(csv_column_name)
        except ValueError:
            raise Error(f'configured column not found in file: {csv_column_name}')
        value = self._row[index]
        return value

    def _get_value_with_regex(self, csv_column_name, csv_column_regex):
        match = re.match(csv_column_regex, self._get_value(csv_column_name))
        if match is None:
            return None
        try:
            return match.group(1)
        except IndexError:
            raise Error(f'missing match group in regex for column: {column_id}')
