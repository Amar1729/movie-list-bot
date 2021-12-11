#!/venv/bin/python3

import logging
import time
from typing import Tuple

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InlineQueryHandler

# local settings.py with KEY (received from BotFather)
from settings import KEY
from movie_list_bot import general
from movie_list_bot.ui import endpoints, interface
from movie_list_bot.db import movies_db


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

LOGGER = logging.getLogger(__name__)

# help info
COMMANDS = """
about - Information about this bot's source code
help - Show help for this bot
list - Show your lists of movies (unwatched and finished)
add - (deprecated) Add movies to your watch list
watched - (deprecated) Add movies to your finished list
finished - (deprecated) Show your finished list
remove - (deprecated) Remove movies from your finished list
update - Update old movie lists (if your chat has any)
"""

# deprecated commands:
"""
/random - Get 3 random movies from your list
"""


INTRO = "Movie List Bot! A bot for keeping track of movies to watch with your friends.\n"

HELP_STRING = INTRO + "Type @movie_list_bot inline to search for movies!\n" + COMMANDS
ABOUT_STRING = INTRO + "https://github.com/Amar1729/movie-list-bot"


def _help(update, context):
    update.message.reply_text(HELP_STRING)


def _about(update, context):
    update.message.reply_text(ABOUT_STRING)


def deprecated_add(update, context):
    update.message.reply_text(
        "This endpoint deprecated. Add movies by searching for them by typing `@movie_list_bot move title`",
        reply_to_message_id=update.effective_message.message_id,
    )


def deprecated_remove(update, context):
    update.message.reply_text(
        "This endpoint temporarily disabled. Removing movies from a list will be re-implemented in the bot's updated interactive interface.",
        reply_to_message_id=update.effective_message.message_id,
    )


def deprecated_list(update, context):
    update.message.reply_text(
        "This endpoint deprecated. Listing watched or finished movies can be done with /list.",
        reply_to_message_id=update.effective_message.message_id,
    )


def list_random(update, context):
    chat_id = update.message.chat_id

    movies = movies_db.get_watchlist(chat_id)
    if movies:
        random.shuffle(movies)
        update.message.reply_text("\n".join(
            movies[:3]
        ))
    else:
        update.message.reply_text("Not enough movies in to-watch list!")


def inline_search(update, context):
    endpoints.inline_search(update, context)


def main():
    updater = Updater(KEY, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("help", _help))
    updater.dispatcher.add_handler(CommandHandler("about", _about))

    updater.dispatcher.add_handler(CommandHandler("add", deprecated_add, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("remove", deprecated_remove, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("random", list_random, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("watched", deprecated_list, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("finished", deprecated_list, pass_args=True))

    # check interface for handled events
    # /list
    # /update
    conv_handler = interface.interface()
    updater.dispatcher.add_handler(conv_handler)

    updater.dispatcher.add_handler(InlineQueryHandler(inline_search))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
