from sqlalchemy import event
# noinspection PyProtectedMember TODO
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# noinspection PyUnusedLocal TODO
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
