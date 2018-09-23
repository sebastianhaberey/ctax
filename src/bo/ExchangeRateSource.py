from sqlalchemy import Column, String, Integer

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

    # short textual description of source
    short_description = Column(String)

    # long textual description of source
    long_description = Column(String)

    def __init__(self, source_id, short_description, long_description):
        self.source_id = source_id
        self.short_description = short_description
        self.long_description = long_description
