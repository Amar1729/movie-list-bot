from pathlib import Path
from typing import List, Optional

# third-party
from sqlalchemy.orm import sessionmaker

# local
from .models import engine, Base, Chat, Movie_IMDB
from .movies import Movies

_P = Path(__file__)
CHAT_DIR = Path(*_P.parts[:-3])

Base.metadata.create_all(engine)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Session = sessionmaker(bind=engine)
session = Session()


def add_movie(**kwargs) -> Movie_IMDB:
    """ Add an IMDB movie to our local db """
    if movie := get_movie(kwargs["id"]):
        return movie

    movie = Movie_IMDB(**kwargs)
    session.add(movie)
    session.commit()
    return movie


def get_movie(movie_id: str) -> Optional[Movie_IMDB]:
    return session.query(Movie_IMDB).filter(Movie_IMDB.id == movie_id).first()


def get_watchlist(chat_id: int) -> List[int]:
    """ Get list of IMDB IDs a chat has on their watchlist """
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        return chat.watch_list
    else:
        return []


def get_watched(chat_id: int) -> List[int]:
    """ Get list of IMDB IDs a chat has on their watchlist """
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        return chat.watched
    else:
        return []


def add_watchlist(chat_id: int, movie_id: int) -> bool:
    """ Add a movie (by ID) to a chat's watchlist.
    Creates a new chat if necessary.
    Returns False if the movie was already on the watchlist.
    """
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        watch_list = chat.watch_list
        if movie_id in watch_list:
            return False
        chat.watch_list.append(movie_id)

        session.commit()
    else:
        watch_list = [movie_id]
        watched: List[int] = []
        chat = Chat(id=chat_id, watch_list=watch_list, watched=watched)

        session.add(chat)
        session.commit()

    return True


def remove_watchlist(chat_id: int, movie_id: int) -> bool:
    """ Remove a move (by ID) from a chat's watchlist.
    Does nothing if the chat does not exist, or the movie isn't on the watchlist.
    If removed, return True; otherwise, returns False.
    """
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        watch_list = chat.watch_list
        if movie_id in watch_list:
            watch_list.remove(movie_id)
            chat.watch_list = watch_list

            session.commit()
            return True

    return False


def checkin(chat_id: int, movie_id: int) -> bool:
    """ Remove a movie (by ID) from a chat's watchlist
    and add it to the watched (finished) list.

    Returns True if movie was on watchlist, False otherwise.
    """
    on_watchlist = remove_watchlist(chat_id, movie_id)
    add_watched(chat_id, movie_id)
    return on_watchlist


def add_watched(chat_id: int, movie_id: int):
    """ Add a movie (by ID) to a chat's watched (finished) list.
    Creates a new chat if necessary.
    Returns False if the movie was already on the watchlist.
    """
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        watched = chat.watched
        if movie_id in watched:
            return False
        chat.watched.append(movie_id)
        session.commit()
    else:
        watch_list: List[int] = []
        watched = [movie_id]
        chat = Chat(id=chat_id, watch_list=watch_list, watched=watched)
        session.add(chat)
        session.commit()

    return True


def deprecated_remove_chat(chat_id: int):
    """ removes a chat's pickle file if it is empty """
    m = Movies(CHAT_DIR)
    g = m._read(chat_id)

    if g.get("list") or g.get("finished"):
        return

    m.remove(chat_id)


def deprecated_get_watchlist(chat_id: int) -> List[str]:
    m = Movies(CHAT_DIR)
    g = m._read(chat_id).get("list", [])
    return g


def deprecated_remove_watchlist(chat_id: int, movie_num: int):
    m = Movies(CHAT_DIR)
    m.remove_movie(chat_id, movie_num)

    deprecated_remove_chat(chat_id)


def deprecated_get_watched(chat_id: int) -> List[str]:
    m = Movies(CHAT_DIR)
    g = m._read(chat_id).get("finished", [])
    return g


def deprecated_remove_watched(chat_id: int, movie_num: int):
    m = Movies(CHAT_DIR)
    g = m._read(chat_id)

    try:
        moviename = g["finished"].pop(movie_num - 1)
        m._update(chat_id, g)
    except IndexError:
    pass

    deprecated_remove_chat(chat_id)