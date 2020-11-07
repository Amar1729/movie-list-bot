#!/venv/bin/python3

import logging
import os
import time
from pathlib import Path
from typing import Tuple

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# local settings.py with KEY (received from BotFather)
from settings import KEY
from db.movies import Movies


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

LOGGER = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(Path(__file__).absolute())

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


MOVIES = Movies(BASE_DIR)


def _help(update, context):
    update.message.reply_text(HELP_STRING)


def list_add(update, context):
    chat_id = update.message.chat_id

    if not context.args:
        update.message.reply_text("Usage: /add <movie title> [# <movie title> ...]")
        return

    for movie in " ".join(context.args).split(" # "):
        if MOVIES.add_movie(chat_id, movie.strip()):
            update.message.reply_text("'{}' added to list".format(movie.strip()))
        else:
            update.message.reply_text("'{}' already on list".format(movie.strip()))


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

def list_list(update, context):
    chat_id = update.message.chat_id

    ret = MOVIES.list_movies(chat_id)
    if ret:
        update.message.reply_text("Your list:\n{}".format(ret))
    else:
        update.message.reply_text("No movie list yet! Add movies with /add.")


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


def list_watched(update, context):
    """
    Mark a movie (index from list, or given by name) as watched.

    Undocumented: add multiple movies by title to the list in one command
    by seperating names with ' # '
    """
    chat_id = update.message.chat_id

    if not context.args:
        update.message.reply_text("Usage: /watched <movie title|index>")
        return

    for movie_or_idx in " ".join(context.args).split(" # "):
        try:
            idx = int(movie_or_idx)
            # remove idx from list
            movie = MOVIES.remove_movie(chat_id, idx)
            if movie:
                # add to finished list
                MOVIES.add_to_watched(chat_id, movie)

                update.message.reply_text(
                    "Added '{}' to your finished list!".format(movie)
                    + " (and removed from watchlist)"
                )

            else:
                update.message.reply_text("/watched: if the movie title is just a number, surround it with quotes to add directly to the finished list")

            # don't remove multiple movies by index in one command
            return

        except ValueError:
            was_removed = MOVIES.watched_a_movie(chat_id, movie_or_idx)
            update.message.reply_text(
                "Added '{}' to your finished list!".format(movie_or_idx)
                + " (and removed from watchlist)" if was_removed else ""
            )


def finished_list(update, context):
    chat_id = update.message.chat_id

    ret = MOVIES.finished_movies(chat_id)
    if ret:
        update.message.reply_text("You've watched: \n{}".format(ret))
    else:
        update.message.reply_text(
            "This chat hasn't finished any movies! Add them with /watched."
        )


def main():
    updater = Updater(KEY, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("help", _help))
    updater.dispatcher.add_handler(CommandHandler("add", list_add, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("remove", list_remove, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("list", list_list))
    updater.dispatcher.add_handler(CommandHandler("random", list_random, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("watched", list_watched, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("finished", finished_list))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
