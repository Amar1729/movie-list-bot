"""
Endpoints and related functions this bot supports.
"""

from uuid import uuid4
from typing import Optional

# third-party
from imdb import IMDb
from imdb import Movie

from telegram import InlineQueryResultArticle, InputTextMessageContent

# local
from . import emoji
from movie_list_bot.constants import WATCH_LIST, WATCHED, CANCEL
from movie_list_bot.db.movies_db import add_movie, get_movie


IA = IMDb()


def _search_imdb(title: str, limit: int = 5):
    counter = 0
    for result in IA.search_movie(title):
        if result.data["kind"] == "movie":
            print("Found movie: {}".format(result["title"]))
            try:
                title = result["title"]
                thumb_url = result["cover url"]
                desc = result["year"]
            except KeyError:
                continue

            yield InlineQueryResultArticle(
                id=uuid4(),
                title=title,
                thumb_url=thumb_url,
                description=desc,
                input_message_content=InputTextMessageContent(result.getID()),
            )

            counter += 1
            if counter > limit:
                break


def search_imdb_keyboard(title: str, limit: int = 10):
    for idx, result in enumerate(IA.search_movie(title)):
        if result.data["kind"] == "movie":
            try:
                title = result["title"]
                # thumb_url = result["cover url"]
                desc = result["year"]
            except KeyError:
                continue

            yield (result.getID(), title, desc)

            if idx > limit:
                break


def _get_imdb_kwargs(movie: Movie.Movie) -> dict[str, Optional[str]]:
    kwargs = {
        "id": movie.getID(),
        "title": movie["title"],
        "thumb_url": movie.get("cover url"),
        "year": movie["year"],
        "runtime": movie["runtime"][0],
        "genres": ", ".join(movie["genres"]),
        "plot_outline": movie.get("plot outline", None),
        "rating": movie["rating"],
        "url": IA.get_imdbURL(movie),
    }

    return kwargs


def short_title(movie_id: str) -> str:
    """ Returns a short slug for a movie_id """
    if movie := get_movie(movie_id):
        return movie.slug()

    movie_result = IA.get_movie(movie_id)
    movie = add_movie(**_get_imdb_kwargs(movie_result))
    return movie.slug()


def create_message(movie_id: str):
    """ Displays a movie, given an IMDB movie ID """
    if movie := get_movie(movie_id):
        return movie.long_description()

    movie_result = IA.get_movie(movie_id, info=["main"])
    movie = add_movie(**_get_imdb_kwargs(movie_result))
    return movie.long_description()


def inline_search(update, context):
    """ Search trakt for a movie """
    # chat_id = update.message.chat_id

    query = update.inline_query.query

    print("dbg:")
    print(query)

    update.inline_query.answer(
        list(_search_imdb(query))
    )
