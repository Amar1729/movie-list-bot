from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList

# local
from movie_list_bot.constants import DB_CONN
from movie_list_bot.ui import emoji


engine = create_engine(DB_CONN)
connection = engine.connect()

# declarative base class
Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True)
    watch_list = Column(MutableList.as_mutable(JSON), default=[])
    watched = Column(MutableList.as_mutable(JSON), default=[])


class Movie_IMDB(Base):
    __tablename__ = "imdb"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    thumb_url = Column(String, nullable=True)
    year = Column(Integer)
    runtime = Column(Integer)
    genres = Column(JSON)
    # plot = Column(String)
    plot_outline = Column(String, nullable=True)
    rating = Column(String)
    # cover_url = Column(String)
    url = Column(String)

    def slug(self) -> str:
        return f"{self.title} // {self.year} // {self.runtime}m"

    def long_description(self) -> str:
        return "\n".join([
            f"{emoji.MOVIE} {self.title}",
            "",
            f"Year: {self.year}",
            "Genres: " + self.genres,
            "",
            # sometimes 'plot outline' isn't there?
            f"Plot\n{self.plot_outline}" if self.plot_outline else "",
            "",
            f"Rating: {self.rating} / 10.0",
            "",
            self.url,
        ])