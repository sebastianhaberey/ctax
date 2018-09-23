from decimal import Decimal

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utc import UtcDateTime

from src.DateUtils import date_and_time_to_string
from src.NumberUtils import scaled_integer_to_decimal, value_to_scaled_integer, currency_to_string
from src.bo.Base import Base
from src.bo.ExchangeRateSource import ExchangeRateSource


class ExchangeRate(Base):
    """
    Represents an exchange rate for a currency pair for a specific time.
    """

    __tablename__ = 'exchange_rate'

    # unique id given by persistence layer
    id = Column(Integer, primary_key=True)

    # the base currency symbol
    base_currency = Column(String)

    # the quote currency symbol
    quote_currency = Column(String)

    # the rate as integer (base amount * rate = quote amount)
    _rate = Column('rate', Integer)

    # time where the exchange rate was valid
    timestamp = Column(UtcDateTime)

    # the transactions this exchange rate is associated with
    transactions = relationship('Transaction')

    # the persistence id of the source that this exchange rate is associated with
    # if an exchange rate source is deleted, all the exchange rates associated with it are deleted too (by DB)
    source_id = Column(Integer, ForeignKey('exchange_rate_source.id', ondelete="CASCADE"))

    # back reference to navigate from exchange rate to source
    source = relationship(ExchangeRateSource)

    def get_rate(self, base_currency, quote_currency):
        """
        Returns the rate to convert between the two currencies.
        :returns: rate or None if one or both currencies do not match
        """
        if (base_currency == self.base_currency) and (quote_currency == self.quote_currency):
            return self.rate
        elif (quote_currency == self.base_currency) and (base_currency == self.quote_currency):
            return Decimal('1') / self.rate
        return None

    def can_convert(self, currency_a, currency_b):
        """
        Returns True if the exchange rate can convert between the two currencys
        """
        return ((currency_a == self.base_currency) and (currency_b == self.quote_currency)) or \
               ((currency_b == self.base_currency) and (currency_a == self.quote_currency))

    @property
    def rate(self):
        return None if self._rate is None else scaled_integer_to_decimal(self._rate, 10)

    @rate.setter
    def rate(self, value):
        self._rate = None if value is None else value_to_scaled_integer(value, 10)

    def __init__(self, base_currency, quote_currency, rate, time, source):
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.rate = rate
        self.timestamp = time
        self.source = source

    def render(self, base_currency, quote_currency):
        return f'{currency_to_string(self.get_rate(base_currency, quote_currency), quote_currency)}/{base_currency} ' \
               f'({self.source.source_id}, {date_and_time_to_string(self.timestamp)})'
