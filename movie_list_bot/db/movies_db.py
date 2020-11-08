from typing import Set

# third-party
from sqlalchemy.orm import sessionmaker

# local
from .models import engine, Base, Chat

Base.metadata.create_all(engine)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Session = sessionmaker(bind=engine)
session = Session()


def get_watchlist(chat_id: int) -> str:
    """ Get list of IMDB IDs a chat has on their watchlist """
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        return chat.watch_list
    else:
        return ""


def get_watched(chat_id: int) -> str:
    """ Get list of IMDB IDs a chat has on their watchlist """
    chat = session.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        return chat.watched
    else:
        return ""


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
        watch_list.update([movie_id])
        chat.watch_list = watch_list

        session.commit()
    else:
        watch_list = set([movie_id])
        watched: Set[int] = set([])
        chat = Chat(id=chat_id, watch_list=watch_list, watched=watched)

        session.add(chat)

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
        watched.update([movie_id])
        chat.watched = watched
        session.commit()
    else:
        watch_list: Set[int] = set([])
        watched = set([movie_id])
        chat = Chat(id=chat_id, watch_list=watch_list, watched=watched)
        session.add(chat)

    return True


class Movies:
    """ Wrapper class for compatibility with old Movies object.
    """
    pass
