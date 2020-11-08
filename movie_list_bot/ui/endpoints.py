"""
Endpoints and related functions this bot supports.
"""

from uuid import uuid4

# third-party
from imdb import IMDb

from telegram import InlineQueryResultArticle, InputTextMessageContent

# local
from . import emoji
from movie_list_bot.constants import WATCH_LIST, WATCHED, CANCEL


IA = IMDb()


def _search_imdb(title: str, limit: int = 5):
    counter = 0
    for result in IA.search_movie(title):
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


def short_title(movie_id: str) -> str:
    """ Returns a short slug for a movie_id """
    movie = IA.get_movie(movie_id)
    return f"{movie['title']} // {movie['year']} // {movie['runtime'][0]}m"


def create_message(movie_id: str):
    """ Displays a movie, given an IMDB movie ID """
    movie = IA.get_movie(movie_id, info=["main"])

    return "\n".join([
        f"{emoji.MOVIE} {movie['title']}",
        "",
        f"Year: {movie['year']}",
        "Genres:" + ", ".join(movie['genres']),
        "",
        # sometimes 'plot outline' isn't there?
        "Plot\n{}".format(movie["plot outline"]) if "plot outline" in movie else "",
        "",
        f"Rating: {movie['rating']} / 10.0",
        "",
        # TODO - can this be formatted as markdown?
        # f"[thumbnail]\\({movie['cover url']}\\)",
        movie["cover url"],
    ])


def inline_search(update, context):
    """ Search trakt for a movie """
    # chat_id = update.message.chat_id

    query = update.inline_query.query

    print("dbg:")
    print(query)

    update.inline_query.answer(
        list(_search_imdb(query))
    )
