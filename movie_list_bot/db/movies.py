import os
import pickle
import random
import sys


class Movies:
    """
    Compatibility class for dealing with (obsolete) pickle files
    """
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    @staticmethod
    def _empty_chat():
        return {"list": [], "finished": []}

    def remove(self, chat_id):
        f = os.path.join(self.base_dir, "chats", "{}.pickle".format(chat_id))
        if os.path.exists(f):
            os.unlink(f)

    def _read(self, chat_id):
        f = os.path.join(self.base_dir, "chats", "{}.pickle".format(chat_id))
        if os.path.exists(f):
            with open(f, "rb") as chatfile:
                g = pickle.load(chatfile)
                return g

        return Movies._empty_chat()

    def _update(self, chat_id, g):
        f = os.path.join(self.base_dir, "chats", "{}.pickle".format(chat_id))
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
        return Movies.display(g["finished"])

    def get_random(self, chat_id, count):
        g = self._read(chat_id)
        random.shuffle(g["list"])
        return Movies.display(g["list"][:count])
