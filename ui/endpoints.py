"""
Endpoints and related functions this bot supports.
"""

from uuid import uuid4

# third-party
from imdb import IMDb

from telegram import InlineQueryResultArticle, InputTextMessageContent


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


def inline_search(update, context):
    """ Search trakt for a movie """
    # chat_id = update.message.chat_id

    query = update.inline_query.query

    print("dbg:")
    print(query)

    update.inline_query.answer(
        list(_search_imdb(query))
    )
