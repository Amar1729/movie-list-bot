from os.path import dirname
from pathlib import Path

from movie_list_bot.db.movies import Movies


BASE_DIR = dirname(dirname(Path(__file__).absolute()))

MOVIES = Movies(BASE_DIR)
