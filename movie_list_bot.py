#!/venv/bin/python3

import logging
import os
import pickle
import random
import sys
import time
from pathlib import Path
from typing import Tuple

import telepot

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
    "/random": "Get __n__ random movies from your list (default returns only one)",
    "/watched": "Tell movie_list_bot you've watched this movie (and remove it from your watchlist)",
    "/finished": "List of movies your group has finished",
    "/help": "Show help for this bot",
}

BOT = telepot.Bot(KEY)



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

    def watched_a_movie(self, chat_id, movie):
        g = self._read(chat_id)

        idx = Movies.contains(g, "list", movie)
        if idx >= 0:
            g["list"].pop(idx)

        if Movies.contains(g, "finished", movie) == -1:
            g["finished"].append(movie)

        self._update(chat_id, g)

    def finished_movies(self, chat_id):
        g = self._read(chat_id)
        return Movies.display(g["finished"][::-1])

    def get_random(self, chat_id, count):
        g = self._read(chat_id)
        random.shuffle(g["list"])
        return Movies.display(g["list"][:count])


MOVIES = Movies()


def _remove_wrapper(chat_id, count: int) -> Tuple[bool, str]:
    movie_name = MOVIES.remove_movie(chat_id, count)
    if movie_name:
        return (True, movie_name)
    else:
        return (
            False,
            "Not enough items in list (invalid number?): {}".format(count),
        )


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

    ret, text = _remove_wrapper(chat_id, count)
    if ret:
        text = "Removed: " + text
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

def finished_list(update, context):
    chat_id = update.message.chat_id

    ret = MOVIES.finished_movies(chat_id)
    if ret:
        update.message.reply_text("You've watched: \n{}".format(ret))
    else:
        update.message.reply_text(
            "This chat hasn't finished any movies! Add them with /watched."
        )


def handle(msg):
    if not ("text" in msg and any(msg["text"].startswith(k) for k in COMMANDS)):
        return

    chat_id = msg["chat"]["id"]
    command = msg["text"]

    print("got command: {}".format(command))

    # Add a movie to the watchlist (creates the group if it didn't exist yet)
    if command.startswith("/add"):
        try:
            first_space = command.index(" ")
            movie_list = command[first_space + 1 :].strip()
        except ValueError:
            movie_list = None

        if not movie_list:
            BOT.sendMessage(chat_id, "Make sure to include a movie title with /add")
        else:
            for movie in movie_list.split("\n"):
                if MOVIES.add_movie(chat_id, movie.strip()):
                    BOT.sendMessage(chat_id, "'{}' added to list".format(movie.strip()))
                else:
                    BOT.sendMessage(
                        chat_id, "'{}' already on list".format(movie.strip())
                    )

    # Get the movie watchlist
    elif command.startswith("/list"):
        ret = MOVIES.list_movies(chat_id)
        if ret:
            BOT.sendMessage(chat_id, "Your list:\n{}".format(ret))
        else:
            BOT.sendMessage(chat_id, "No movie list yet! Add movies with /add.")

    # Get the list of finished movies
    elif command.startswith("/finished"):
        ret = MOVIES.finished_movies(chat_id)
        if ret:
            BOT.sendMessage(chat_id, "You've watched: \n{}".format(ret))
        else:
            BOT.sendMessage(
                chat_id, "This chat hasn't finished any movies! Add them with /watched."
            )

    elif command.startswith("/random"):
        try:
            count = int(command.split(" ")[1])
        except ValueError:
            BOT.sendMessage(chat_id, "Argument `n` must be an integer")
            return
        except IndexError:
            count = 1

        movie_list = MOVIES.get_random(chat_id, count)
        if movie_list:
            BOT.sendMessage(chat_id, movie_list)
        else:
            BOT.sendMessage(
                chat_id,
                "Not enough movies ({}) in movie list! Check with /list.".format(count),
            )

    # Mark a movie as watched
    elif command.startswith("/watched"):
        try:
            first_space = command.index(" ")
            movie_list = command[first_space + 1 :].strip()
        except ValueError:
            movie_list = None

        if not movie_list:
            BOT.sendMessage(chat_id, "Make sure to include a movie title with /watched")
        else:
            for movie in movie_list.split("\n"):
                MOVIES.watched_a_movie(chat_id, movie)
                BOT.sendMessage(
                    chat_id, "Added '{}' to your finished list!".format(movie)
                )

    elif command.startswith("/modify"):
        first_space = command.index(" ")
        movienum = command[first_space + 1 :]

        pass

    elif command.startswith("/remove"):
        try:
            movie_num = int(command.split(" ")[1])
            movie_name = MOVIES.remove_movie(chat_id, movie_num)
            if movie_name:
                BOT.sendMessage(chat_id, "Removed '{}'".format(movie_name))
            else:
                BOT.sendMessage(
                    chat_id,
                    "Not enough items in list (invalid number?): {}".format(movie_num),
                )
        except (IndexError, ValueError):
            BOT.sendMessage(chat_id, "/remove requires a list item's number.")

    # help string
    elif command.startswith("/help"):
        intro = "Movie List BOT! A BOT for keeping track of movies to watch with your friends."
        help_string = (
            intro
            + "\n"
            + "\n".join("{}: {}".format(c[0], c[1]) for c in COMMANDS.items())
        )
        BOT.sendMessage(chat_id, help_string)


def main():
    updater = Updater(KEY, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("add", list_add, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("remove", list_remove, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("list", list_list))
    updater.dispatcher.add_handler(CommandHandler("random", list_random, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("finished", finished_list))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
