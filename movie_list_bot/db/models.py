from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, PickleType
from sqlalchemy.ext.declarative import declarative_base

# local
from movie_list_bot.constants import DB_CONN


engine = create_engine(DB_CONN)
connection = engine.connect()

# declarative base class
Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True)
    watch_list = Column(PickleType)
    watched = Column(PickleType)
