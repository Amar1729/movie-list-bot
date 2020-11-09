#!/venv/bin/python3

import logging
import time
from typing import Tuple

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InlineQueryHandler

# local settings.py with KEY (received from BotFather)
from settings import KEY
from . import MOVIES
from movie_list_bot import general
from movie_list_bot.ui import endpoints, interface


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

LOGGER = logging.getLogger(__name__)

# help info
COMMANDS = {
    "/add": "Add a movie to your watchlist",
    "/list": "List of movies to watch",
    "/remove": "Remove a a movie from your watchlist (by number)",
    "/random": "Get `n` random movies from your list (default returns only one)",
    "/watched": "Tell movie_list_bot you've watched this movie (and remove it from your watchlist)",
    "/finished": "List of movies your group has finished",
    "/help": "Show help for this bot",
}

INTRO = "Movie List Bot! A bot for keeping track of movies to watch with your friends.\n"
HELP_STRING = (
    INTRO
    + "\n".join("{}: {}".format(c[0], c[1]) for c in COMMANDS.items())
)


def _help(update, context):
    update.message.reply_text(HELP_STRING)


def deprecated_add(update, context):
    update.message.reply_text("This endpoint deprecated. Add movies by searching for them by typing `@movie_list_bot move title`")


def list_remove(update, context):
    chat_id = update.message.chat_id

    try:
        count = int(context.args[0])
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /remove <list index>")
        return

    movie = MOVIES.remove_movie(chat_id, count)
    if movie:
        text = "Removed: " + movie
    else:
        text = "Not enough items in list (invalid number?): {}".format(count)
    update.message.reply_text(text)

def list_random(update, context):
    chat_id = update.message.chat_id

    try:
        count = int(context.args[0])
    except ValueError:
        update.message.reply_text("Usage: /random [<number>]")
        # count = 1
        return
    except IndexError:
        count = 1

    movie_list = MOVIES.get_random(chat_id, count)
    if movie_list:
        update.message.reply_text(movie_list)
    else:
        update.message.reply_text(
            "Not enough movies ({}) in movie list! Check with /list.".format(count),
        )


def inline_search(update, context):
    endpoints.inline_search(update, context)


def main():
    updater = Updater(KEY, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("help", _help))
    updater.dispatcher.add_handler(CommandHandler("add", deprecated_add, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("remove", list_remove, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("random", list_random, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("watched", deprecated_add, pass_args=True))

    conv_handler = interface.interface()
    updater.dispatcher.add_handler(conv_handler)

    updater.dispatcher.add_handler(InlineQueryHandler(inline_search))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
