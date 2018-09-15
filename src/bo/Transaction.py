import enum

from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utc import UtcDateTime

from src.EqualityUtils import equals, calculate_hash
from src.NumberUtils import scaled_integer_to_decimal, value_to_scaled_integer, currency_to_string
from src.bo.ExchangeRate import ExchangeRate
from src.bo.Base import Base


class TransactionType(enum.Enum):
    """
    Type of transaction this group represents.
    """
    BUY = 0
    SELL = 1
    FEE = 2


class Transaction(Base):
    """
    Represents a single transaction, i.e. addition or deduction of money from somewhere.
    """

    __tablename__ = 'transaction'

    # __table_args__ = (ForeignKeyConstraint(['exchange_rate_id'], ['exchange_rate.id'], ondelete="SET NULL"),)

    # unique id given by persistence layer
    id = Column(Integer, primary_key=True)

    # trade id (foreign key) given by persistence layer
    # if a trade is deleted, all the transactions associated with it are deleted too (by DB)
    trade_id = Column(Integer, ForeignKey('trade.id', ondelete="CASCADE"))

    # type of transaction, e.g. BUY, SELL, FEE
    type = Column(Enum(TransactionType))

    # the amount as integer
    _amount = Column('amount', Integer)

    # the currency symbol (e.g. BTC)
    currency = Column(String)

    # the time of transaction
    timestamp = Column(UtcDateTime)

    # the amount converted to tax currency
    _taxable_amount = Column('tax_amount', Integer)

    # the persistence id of the (tax currency) exchange rate that this transaction is associated with
    # if exchange rates are deleted, the foreign key here is set to NULL by DB
    exchange_rate_id = Column(Integer, ForeignKey('exchange_rate.id', ondelete="SET NULL"))

    # back reference to navigate from transaction to exchange rate
    exchange_rate = relationship(ExchangeRate, back_populates="transactions")

    @property
    def amount(self):
        return None if self._amount is None else scaled_integer_to_decimal(self._amount, 10)

    @amount.setter
    def amount(self, value):
        self._amount = None if value is None else value_to_scaled_integer(value, 10)

    @property
    def taxable_amount(self):
        return None if self._taxable_amount is None else scaled_integer_to_decimal(self._taxable_amount, 10)

    @taxable_amount.setter
    def taxable_amount(self, value):
        self._taxable_amount = None if value is None else value_to_scaled_integer(value, 10)

    def get_equality_relevant_items(self):
        # id and group id are not relevant because they are set by the persistence layer
        # and will not be available in all situations, leading to false negatives
        return [self.type, self._amount, self.currency]

    def __eq__(self, other):
        return equals(self, other)

    def __hash__(self):
        return calculate_hash(self)

    def __str__(self) -> str:
        return f'id: {self.id}, type: {self.type.name}, ' \
               f'amount: {currency_to_string(self.amount, self.currency)}'

    def render_with_tax(self, tax_currency):

        out = f'{self}'

        if self.exchange_rate is not None:
            out += ', '
            out += f'exchange rate: {self.exchange_rate.render(self.currency, tax_currency)}'

        if self.taxable_amount is not None:
            out += ', '
            out += f'taxable amount: {currency_to_string(self.taxable_amount, tax_currency)}'

        return out
