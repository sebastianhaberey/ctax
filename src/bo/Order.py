from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from src.EqualityUtils import equals, calculate_hash
from src.bo.Base import Base
from src.bo.Trade import get_earliest_trade


def sort_orders_by_time(orders):
    """
    Sorts orders by timestamp of their trades (order with earliest trade first).
    """
    return sorted(orders, key=lambda order: get_earliest_trade(order.trades).timestamp)


class Order(Base):
    """
    Represents an order on an exchange.
    """

    __tablename__ = 'order'

    # unique id given by persistence layer
    id = Column(Integer, primary_key=True)

    # list of trades belonging to the order
    trades = relationship('Trade')

    # id from source (i.e. exchange)
    source_id = Column(String)

    # a textual representation of the exchange this order belongs to
    exchange = Column(String)

    def __init__(self, source_id, exchange):
        self.source_id = source_id
        self.exchange = exchange

    def get_equality_relevant_items(self):
        items = [self.source_id, self.exchange]
        if self.trades is not None:
            items.extend(self.trades)
        return items

    def __eq__(self, other):
        return equals(self, other, relaxed_order=True)  # trades may vary in order because of DB

    def __hash__(self):
        return calculate_hash(self)

    def __str__(self) -> str:
        return f'id: {self.id}, source id: {self.source_id}, exchange: {self.exchange}'
