from typing import Set

from movie_list_bot.db import movies_db
from movie_list_bot.ui.endpoints import short_title


def _list_movies(ret: Set[int]) -> str:
    return "\n".join([
        f"{idx+1}: {short_title(movie_id)}"
        for idx, movie_id in enumerate(ret)
    ])


def list_watchlist(movies, chat_id) -> str:
    """ Get movies on a chat's watchlist """
    ret = movies_db.get_watchlist(chat_id)
    if ret:
        return "To-watch list:\n" + _list_movies(ret)
    else:
        return "No movie list yet! Add movies with /add."


def list_watched(movies, chat_id) -> str:
    """ Get movies a chat has finished """
    ret = movies_db.get_watched(chat_id)
    if ret:
        return "Finished movies: \n" + _list_movies(ret)
    else:
        return "This chat hasn't finished any movies! Add them with /add."


def add_watchlist(movies, movie_id, chat_id):
    """ Add a movie by IMDB ID to a chat's to-watch list """
    if movies_db.add_watchlist(chat_id, movie_id):
        return "'{}' added to watch list".format(short_title(movie_id))
    else:
        return "'{}' already on watch list".format(short_title(movie_id))


def add_watched(movies, movie_id, chat_id):
    """ Add a movie by IMDB ID to a chat's finished (watched) list """
    was_removed = movies_db.checkin(chat_id, movie_id)
    return "Added '{}' to your watched (finished) list!{}".format(
        short_title(movie_id), " (and removed from watch list)" if was_removed else ""
    )
