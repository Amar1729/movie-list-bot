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
from movie_list_bot.constants import SEARCH, WATCH_LIST, WATCHED, CANCEL, SEP
from movie_list_bot import general
from movie_list_bot.ui import endpoints


# stages for the interface
FIRST, SECOND = range(2)
# callback data
ONE, TWO, THREE, FOUR = map(str, range(4))


def start(update, context):
    keyboard = [
        # TODO - can i switch to inline and then come back to the convo?
        [InlineKeyboardButton(SEARCH, switch_inline_query_current_chat="")],
        [
            InlineKeyboardButton(WATCH_LIST, callback_data=TWO),
            InlineKeyboardButton(WATCHED, callback_data=THREE),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Choose:", reply_markup=reply_markup)

    return FIRST


def list_movies(update, context):
    keyboard = [
        [
            InlineKeyboardButton(WATCH_LIST, callback_data=TWO),
            InlineKeyboardButton(WATCHED, callback_data=THREE),
        ],
        [InlineKeyboardButton(CANCEL, callback_data=FOUR)],
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

    keyboard = [
        [
            InlineKeyboardButton(WATCH_LIST, callback_data=TWO + SEP + imdb_id),
            InlineKeyboardButton(WATCHED, callback_data=THREE + SEP + imdb_id),
        ],
        [InlineKeyboardButton(CANCEL, callback_data=FOUR)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    content = endpoints.create_message(movie_id=imdb_id)
    update.message.reply_text(
        content,
        reply_to_message_id=update.effective_message.message_id,
        reply_markup=reply_markup
    )

    return SECOND


def end_convo_wrapper(msg, update, context):
    """ Ends a conversation with text 'msg' """
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=msg)
    return ConversationHandler.END


def _show_watch_list(update, context):
    chat_id = update.effective_chat["id"]
    return end_convo_wrapper(general.list_watchlist(chat_id), update, context)


def _show_watched(update, context):
    chat_id = update.effective_chat["id"]
    return end_convo_wrapper(general.list_watched(chat_id), update, context)


def _add_watch_list(update, context):
    chat_id = update.effective_chat["id"]
    query = update.callback_query
    movie_id = query["message"]["reply_markup"]["inline_keyboard"][0][0]["callback_data"].split(SEP)[1]

    result_txt = general.add_watchlist(movie_id, chat_id)
    return end_convo_wrapper(result_txt, update, context)


def _add_watched(update, context):
    chat_id = update.effective_chat["id"]
    query = update.callback_query
    movie_id = query["message"]["reply_markup"]["inline_keyboard"][0][1]["callback_data"].split(SEP)[1]

    result_txt = general.add_watched(movie_id, chat_id)
    return end_convo_wrapper(result_txt, update, context)


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
            # TODO - have to implement switching between MarkupKeyboard / InlineQuery ?
            # CommandHandler("start", start),
            CommandHandler("list", list_movies),
            MessageHandler(Filters.via_bot(username=set(["movie_list_bot"])), handle_movie)
        ],
        states={
            FIRST: [
                CallbackQueryHandler(_show_watch_list, pattern='^' + TWO + '$'),
                CallbackQueryHandler(_show_watched, pattern='^' + THREE + '$'),
                CallbackQueryHandler(end, pattern='^' + FOUR + '$'),
            ],
            SECOND: [
                CallbackQueryHandler(_add_watch_list, pattern='^' + TWO + SEP),
                CallbackQueryHandler(_add_watched, pattern='^' + THREE + SEP),
                CallbackQueryHandler(end, pattern='^' + FOUR + '$'),
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    return conv_handler
