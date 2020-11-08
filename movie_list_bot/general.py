def list_watchlist(movies, chat_id) -> str:
    """ Get movies on a chat's watchlist """
    ret = movies.list_movies(chat_id)
    if ret:
        return "Your list:\n{}".format(ret)
    else:
        return "No movie list yet! Add movies with /add."


def list_watched(movies, chat_id) -> str:
    """ Get movies a chat has finished """
    ret = movies.finished_movies(chat_id)
    if ret:
        return "You've watched: \n{}".format(ret)
    else:
        return "This chat hasn't finished any movies! Add them with /watched."
