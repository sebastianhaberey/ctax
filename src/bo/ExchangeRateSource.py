from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from src.bo.Base import Base


class ExchangeRateSource(Base):
    """
    Represents a source for exchange rates (website, file or similar).
    """

    __tablename__ = 'exchange_rate_source'

    # unique id given by persistence layer
    id = Column(Integer, primary_key=True)

    # user-side id to describe the source
    source_id = Column(String)

    # textual description of source
    description = Column(String)

    def __init__(self, source_id, description):
        self.source_id = source_id
        self.description = description
