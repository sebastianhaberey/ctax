from functools import reduce

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utc import UtcDateTime

from src.DateUtils import date_and_time_to_string
from src.EqualityUtils import equals, calculate_hash
from src.Error import Error
from src.bo.Base import Base


def sort_trades_by_time(trades):
    """
    Sorts list of trades by time (earliest first).
    """
    return sorted(trades, key=lambda trade: trade.timestamp)


def get_earliest_trade(trades):
    """
    Gets the earliest trade from a list of trades.
    """

    return reduce(lambda trade_a, trade_b: trade_a if trade_a.timestamp < trade_b.timestamp else trade_b, trades)


class Trade(Base):
    """
    Represents a trade on an exchange.
    """

    __tablename__ = 'trade'

    # unique id given by persistence layer
    id = Column(Integer, primary_key=True)

    # order id (foreign key) given by persistence layer
    # if an order is deleted, all the trades associated with it are deleted too (by DB)
    order_id = Column(Integer, ForeignKey('order.id', ondelete="CASCADE"))

    # trade id as given by source (i.e. exchange)
    source_id = Column(String)

    # the time of trade
    timestamp = Column(UtcDateTime)

    # list of transactions belonging to the trade
    # this could currently be replaced by three one-to-one relationships (sell, buy, fee),
    # but it's likely there will be more than one fee per transaction in future versions
    transactions = relationship("Transaction")

    def __init__(self, source_id, timestamp, transactions):
        self.source_id = source_id
        self.timestamp = timestamp
        if transactions is not None:
            self.transactions.extend(transactions)

    def __str__(self) -> str:
        return f'id: {self.id}, ' \
               f'source id: {self.source_id}, ' \
               f'timestamp: {date_and_time_to_string(self.timestamp)}'

    def get_equality_relevant_items(self):
        items = [self.source_id, self.timestamp]
        if self.transactions is not None:
            items.extend(self.transactions)
        return items

    def get_transaction(self, transaction_type):
        results = self._get_transactions(transaction_type)
        count = len(results)
        if count != 1:
            raise Error(f'expected exactly one transaction of type {transaction_type.name}, but got {count}')
        return results[0]

    def _get_transactions(self, transaction_type):
        return list(filter(lambda transaction: transaction.type == transaction_type, self.transactions))

    def __eq__(self, other):
        return equals(self, other, relaxed_order=True)  # order of transactions may vary because of DB

    def __hash__(self):
        return calculate_hash(self)
