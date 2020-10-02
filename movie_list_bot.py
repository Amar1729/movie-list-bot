#!/venv/bin/python3

import logging
import os
import pickle
import random
import sys
import time
from pathlib import Path
from typing import Tuple

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# local settings.py with KEY (received from BotFather)
from settings import KEY


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


class Movies:
    def __init__(self):
        pass

    def _empty_chat():
        return {"list": [], "finished": []}

    def _read(self, chat_id):
        f = os.path.join(BASE_DIR, "chats", "{}.pickle".format(chat_id))
        if os.path.exists(f):
            with open(f, "rb") as chatfile:
                g = pickle.load(chatfile)
                return g

        return self._empty_chat()

    def _update(self, chat_id, g):
        f = os.path.join(BASE_DIR, "chats", "{}.pickle".format(chat_id))
        try:
            with open(f, "wb") as chatfile:
                pickle.dump(g, chatfile)
        except Exception as e:
            print("Could not write chat to disk. Exiting.")
            print(e)
            sys.exit(1)

    @staticmethod
    def contains(g, target, movie):
        assert target in ["list", "finished"]
        try:
            return list(map(lambda e: e.lower(), g[target])).index(movie.lower())
        except ValueError:
            return -1

    @staticmethod
    def display(movie_list):
        return "\n".join(
            ["{}: {}".format(idx + 1, movie) for idx, movie in enumerate(movie_list)]
        )

    def add_movie(self, chat_id, movie):
        g = self._read(chat_id)
        if Movies.contains(g, "list", movie) == -1:
            g["list"].append(movie)
            self._update(chat_id, g)
            return True
        return False

    def remove_movie(self, chat_id, movienum):
        g = self._read(chat_id)
        try:
            moviename = g["list"].pop(movienum - 1)
            self._update(chat_id, g)
            return moviename
        except IndexError:
            return ""

    def list_movies(self, chat_id):
        g = self._read(chat_id)
        return Movies.display(g["list"])

    def add_to_watched(self, chat_id, movie):
        g = self._read(chat_id)

        if Movies.contains(g, "finished", movie) == -1:
            g["finished"].append(movie)

        self._update(chat_id, g)

    def watched_a_movie(self, chat_id, movie) -> bool:
        g = self._read(chat_id)

        idx = Movies.contains(g, "list", movie)
        if idx >= 0:
            g["list"].pop(idx)
            ret = True
        else:
            ret = False

        self._update(chat_id, g)
        self.add_to_watched(chat_id, movie)
        return ret

    def finished_movies(self, chat_id):
        g = self._read(chat_id)
        return Movies.display(g["finished"][::-1])

    def get_random(self, chat_id, count):
        g = self._read(chat_id)
        random.shuffle(g["list"])
        return Movies.display(g["list"][:count])


MOVIES = Movies()


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
