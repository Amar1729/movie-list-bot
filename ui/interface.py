"""
Manage the interactive interface for this bot:
Searching movie / adding them to watch/finished lists
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup  # , ParseMode
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)

# local
from . import endpoints, emoji


SEARCH = f"{emoji.SEARCH} Search"
WATCHED = f"{emoji.EYES} Watched"
WATCH_LIST = f"{emoji.MOVIE} Watch List"
CANCEL = f"{emoji.REDX} Cancel"


# stages for the interface
FIRST, SECOND = range(2)
# callback data
ONE, TWO, THREE, FOUR = map(str, range(4))


def start(update, context):
    keyboard = [
        [InlineKeyboardButton(SEARCH, callback_data=ONE)],
        [
            InlineKeyboardButton(WATCHED, callback_data=TWO),
            InlineKeyboardButton(WATCH_LIST, callback_data=THREE),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Choose:", reply_markup=reply_markup)

    return FIRST


def handle_movie(update, context):
    """ After a user searches for a movie with this bot,
    we send the IMDB ID directly to chat. If that happens,
    handle adding it to the group's watched or watch lists.
    """
    imdb_id = update.message.text

    content = endpoints.create_message(imdb_id)
    update.message.reply_text(content)

    keyboard = [
        [
            InlineKeyboardButton(WATCH_LIST, callback_data=TWO),
            InlineKeyboardButton(WATCHED, callback_data=THREE),
        ],
        [InlineKeyboardButton(CANCEL, callback_data=FOUR)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Add to:", reply_markup=reply_markup)

    return SECOND


def _todo(msg, update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=msg)
    return ConversationHandler.END


def search(update, context):
    return _todo("search", update, context)


def _show_watched(update, context):
    return _todo("finished list", update, context)


def _show_watch_list(update, context):
    return _todo("watch list", update, context)


def _add_watched(update, context):
    return _todo("add watched", update, context)


def _add_watch_list(update, context):
    return _todo("add watched list", update, context)


def end(update, context):
    query = update.callback_query
    query.answer()
    # is there a way to remove the keyboard markup without sending a msg?
    # these two don't work ...
    # query.delete()
    # update.message.delete()
    query.edit_message_text(text="Finished")
    return ConversationHandler.END


def interface():
    """
    Main handler for the bot interface.
    """
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(Filters.via_bot(username=set(["movie_list_bot"])), handle_movie)
        ],
        states={
            FIRST: [
                CallbackQueryHandler(search, pattern='^' + ONE + '$'),
                CallbackQueryHandler(_show_watched, pattern='^' + TWO + '$'),
                CallbackQueryHandler(_show_watch_list, pattern='^' + THREE + '$'),
            ],
            SECOND: [
                CallbackQueryHandler(_add_watched, pattern='^' + TWO + '$'),
                CallbackQueryHandler(_add_watch_list, pattern='^' + THREE + '$'),
                CallbackQueryHandler(end, pattern='^' + FOUR + '$'),
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    return conv_handler
