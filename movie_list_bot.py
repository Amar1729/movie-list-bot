#!/venv/bin/python3

import configparser
import os
import pickle
import sys
import time
from pathlib import Path

import telepot


BASE_DIR = os.path.dirname(Path(__file__).absolute())

# help info
COMMANDS = {
    "/add": "Add a movie to your watchlist",
    "/list": "List of movies to watch",
    "/remove": "Remove a a movie from your watchlist (by number)",
    "/watched": "Tell movie_list_bot you've watched this movie (and remove it from your watchlist)",
    "/finished": "List of movies your group has finished",
    "/help": "Show help for this bot",
}


class Movies:
    def __init__(self):
        pass

    def _empty_chat():
        return {"list":[], "finished":[]}

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
        return movie.lower() in map(lambda e: e.lower(), g[target])

    @staticmethod
    def display(movie_list):
        return "\n".join([
            "{}: {}".format(idx+1, movie)
            for idx, movie in enumerate(movie_list)
        ])

    def add_movie(self, chat_id, movie):
        g = self._read(chat_id)
        if not Movies.contains(g, "list", movie):
            g["list"].append(movie)
            self._update(chat_id, g)
            return True
        return False

    def remove_movie(self, chat_id, movienum):
        f = os.path.join('chats',str(chat_id))

        new_list = []
        finished = []
        with open(f, "rb") as chatfile:
            g = pickle.load(chatfile)
            finished = g["finished"]
            new_list = list(map(
                lambda e: e[1],
                list(filter(lambda e: e[0] != int(movienum)-1, enumerate(g["list"])))
            ))

        with open(f, "wb") as chatfile:
            g = {}
            g["list"] = new_list
            g["finished"] = finished
            pickle.dump(g, chatfile)

        return 0

    def list_movies(self, chat_id):
        g = self._read(chat_id)
        return Movies.display(g["list"])

    def watched_a_movie(self, chat_id, movie):
        f = os.path.join('chats',str(chat_id))

        try:
            chatfile = open(f, 'rb')

            g = pickle.load( chatfile )
            old_list = g['list']
            finished = g['finished']
            if movie in old_list:
                old_list.remove(movie)
            if movie not in finished:
                finished.append(movie)

            chatfile.close()
            chatfile = open(f, 'wb')
            pickle.dump(g, chatfile)
            chatfile.close()

        except (EOFError, IOError, FileNotFoundError) as e:
            # file is empty (what?)
            chatfile = open(f, 'wb')

            g = {}
            g['list'] = []
            g['finished'] = [movie]

            pickle.dump(g, chatfile)
            chatfile.close()

            return 0
        
    def finished_movies(self, chat_id):
        g = self._read(chat_id)
        return Movies.display(g["finished"][::-1])


movies = Movies()

def handle(msg):
    if not ("text" in msg and any(msg["text"].startswith(k) for k in COMMANDS)):
        return

    chat_id = msg['chat']['id']
    command = msg['text']

    print("got command: {}".format(command))

    # Add a movie to the watchlist (creates the group if it didn't exist yet)
    if command[:4] == '/add':
        first_space = command.index(' ')
        moviename = command[first_space+1:].strip()
        if not moviename:
            bot.sendMessage(chat_id, "Make sure to include a movie title with /add")
        else:
            for movie in moviename.split("\n"):
                if movies.add_movie(chat_id, movie.strip()):
                    bot.sendMessage(chat_id, "'{}' added to list".format(movie.strip()))
                else:
                    bot.sendMessage(chat_id, "'{}' already on list".format(movie.strip()))

    # Get the movie watchlist
    elif command.startswith("/list"):
        ret = movies.list_movies(chat_id)
        if ret:
            bot.sendMessage(chat_id, "Your list:\n{}".format(ret))
        else:
            bot.sendMessage(chat_id, "No movie list yet! Add movies with /add.")

    # Get the list of finished movies
    elif command.startswith("/finished"):
        ret = movies.finished_movies(chat_id)
        if ret:
            bot.sendMessage(chat_id, "You've watched: \n{}".format(ret))
        else:
            bot.sendMessage(chat_id, "This chat hasn't finished any movies! Add them with /watched.")

    # Mark a movie as watched
    elif command[:8] == '/watched':
        first_space = command.index(' ')
        moviename = command[first_space+1:]

        if not moviename.strip():
            bot.sendMessage(chat_id, "Make sure to include a movie title with /watched")
        else:
            for movie in moviename.split("\n"):
                movies.watched_a_movie(chat_id, movie)
                bot.sendMessage(chat_id, "Added {} to your finished list!".format(movie))

    elif command[:7] == '/modify':
        first_space = command.index(' ')
        movienum = command[first_space+1:]

        pass

    elif command.startswith("/remove"):
        try:
            movie_num = command.split(" ")[1]
            movies.remove_movie(chat_id, movie_num)
            bot.sendMessage(chat_id, "removed {}".format(movie_num))
        except IndexError:
            bot.sendMessage(chat_id, "/remove endpoint requires a number.")

    # help string
    elif command[:5] == '/help':
        intro = "Movie List Bot! A bot for keeping track of movies to watch with your friends."
        help_string = intro + "\n" + "\n".join("{}: {}".format(c[0], c[1]) for c in COMMANDS.items())
        bot.sendMessage(chat_id, help_string)


config = configparser.ConfigParser()
config.read('config.ini')
key = config['DEFAULT']['key']
bot = telepot.Bot(key)

bot.message_loop(handle)
print("i'm listening yo")

while 1:
    time.sleep(10)
