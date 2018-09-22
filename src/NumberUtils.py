from decimal import Decimal, getcontext, InvalidOperation

DEFAULT_PRECISION = 28  # 28 is python 3 default

DEFAULT_OUTPUT_PRECISION = 2  # default precision for human readable output

# set decimal precision globally
getcontext().prec = DEFAULT_PRECISION

PRECISIONS = {
    'ETH': '5',
    'BTC': '5',
}


def remove_exponent(value, precision=DEFAULT_PRECISION):
    """
    Removes exponent or trailing zeroes for better readability.
    https://stackoverflow.com/a/18769210
    """
    integral_value = value.to_integral_value()

    # only remove exponent if integral value is actually representable without exponent
    # (has to be lower than 10 ^ precision)
    if value == integral_value and integral_value < Decimal(pow(10, precision)):
        return value.quantize(Decimal(1))
    else:
        return value.normalize()


def value_to_decimal(value, precision=DEFAULT_PRECISION):
    """
    Converts a numeric value of arbitrary type to a Decimal, rounding if the input precision is smaller than the
    specified precision.
    :param value: arbitrary numeric value, can be None
    :param precision: precision
    """

    if value is None:
        return None

    if isinstance(value, str) or isinstance(value, int):
        try:
            numeric_value = Decimal(value)
        except InvalidOperation:
            raise ValueError(f'"{value}" is not a valid number.')
    else:
        numeric_value = value

    return remove_exponent(Decimal('{:0.{precision}f}'.format(numeric_value, precision=precision)))


def value_to_string(value, precision=DEFAULT_PRECISION):
    """
    Renders an arbitrary numeric value to a string with the specified precision, rounding if neccessary.
    :param value: numeric value
    :param precision: precision
    """

    if value is None:
        return None

    return '{:0.{precision}f}'.format(value_to_decimal(value), precision=precision)


def value_to_scaled_integer(value, precision=DEFAULT_PRECISION):
    """
    Converts a numeric value to a scaled integer.
    Can be used to persist decimal values as integer where a decimal type is not available.
    :param value: arbitrary numeric value, can be None
    :param precision: precision / scaling factor
    :return: the scaled integer
    """

    if value is None:
        return None

    return int(value_to_string(value, precision).replace('.', ''))


def scaled_integer_to_decimal(value, precision=DEFAULT_PRECISION):
    """
    Converts a scaled integer to a decimal value.
    :param value: scaled integer value, can be None
    :param precision: precision / scale
    :return: decimal value
    """

    if value is None:
        return None

    decimal = value_to_decimal(value)
    return decimal / Decimal(pow(10, precision))


def currency_to_string(value, currency=None, no_symbol=False):
    """
    Returns a human readable representation of the specified value with correct precision and currency symbol.
    Example: '192.50000 BTC'
    """
    currency_string = value_to_string(value, get_precision(currency, DEFAULT_OUTPUT_PRECISION))

    if currency is None or no_symbol is True:
        return currency_string

    return f'{currency_string} {currency}'


def get_precision(currency, default):
    if currency in PRECISIONS:
        return PRECISIONS[currency]
    else:
        return default
