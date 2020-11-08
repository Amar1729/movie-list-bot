from typing import List

from movie_list_bot.ui.endpoints import short_title


def _list_movies(ret: List[str]) -> str:
    return "\n".join([
        f"{idx+1}: {short_title(movie_id)}"
        for idx, movie_id in enumerate(ret)
    ])


def list_watchlist(movies, chat_id) -> str:
    """ Get movies on a chat's watchlist """
    ret = movies._read(chat_id)["list"]
    if ret:
        return "To-watch list:\n" + _list_movies(ret)
    else:
        return "No movie list yet! Add movies with /add."


def list_watched(movies, chat_id) -> str:
    """ Get movies a chat has finished """
    ret = movies._read(chat_id)["finished"]
    if ret:
        return "Finished movies: \n" + _list_movies(ret)
    else:
        return "This chat hasn't finished any movies! Add them with /add."


def add_watchlist(movies, movie_id, chat_id):
    """ Add a movie by IMDB ID to a chat's to-watch list """
    if movies.add_movie(chat_id, movie_id.strip()):
        return "'{}' added to list".format(short_title(movie_id))
    else:
        return "'{}' already on list".format(short_title(movie_id))


def add_watched(movies, movie_id, chat_id):
    """ Add a movie by IMDB ID to a chat's finished (watched) list """
    was_removed = movies.watched_a_movie(chat_id, movie_id)
    return "Added '{}' to your finished list!{}".format(
        short_title(movie_id), " (and removed from watch list)" if was_removed else ""
    )
