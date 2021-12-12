"""
Manage the interactive interface for this bot:
Searching movie / adding them to watch/finished lists
"""

from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup  # , ParseMode
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)

# local
from movie_list_bot.constants import SEARCH, WATCH_LIST, WATCHED, CANCEL, SKIP, SEP
from movie_list_bot import general
from movie_list_bot.ui import endpoints
from movie_list_bot.db.movies_db import (
    deprecated_get_watchlist,
    deprecated_remove_watchlist,
    deprecated_get_watched,
    deprecated_remove_watched,
)


# stages for the interface
class STATES(Enum):
    SHOW = 1
    ADD = 2
    ADD_INLINE = 3


# callback data
ONE, TWO, THREE, FOUR, FIVE = map(str, range(5))


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

    return STATES.SHOW


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

    return STATES.SHOW


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

    return STATES.ADD


def update_helper(update, context) -> int:
    chat_id = update.effective_chat.id

    old_watchlist = deprecated_get_watchlist(chat_id)
    old_finished = deprecated_get_watched(chat_id)

    if not old_watchlist and not old_finished:
        update.message.reply_text(
            "This chat doesn't have any saved movies in the v1 database. Continue using as normal!",
            reply_to_message_id=update.effective_message.message_id,
        )

        return ConversationHandler.END

    if old_watchlist:
        update.message.reply_text(
            "Ok, updating from old database. Starting with your watchlist."
        )

        markups = []
        for movie_idx, movie_title in enumerate(old_watchlist):
            keyboard = [
                [InlineKeyboardButton(f"({year}) {title}", callback_data=f"{TWO}{SEP}{imdb_id}{SEP}{movie_idx}")]
                for imdb_id, title, year in endpoints.search_imdb_keyboard(movie_title)
            ] + [
                [
                    InlineKeyboardButton(CANCEL, callback_data=FOUR),
                    InlineKeyboardButton(SKIP, callback_data=FIVE),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            markups.append(reply_markup)

            # break

        for m in markups:
            update.message.reply_text(
                "\n".join(old_watchlist),
                reply_to_message_id=update.effective_message.message_id,
                reply_markup=m,
            )
            break

        return STATES.ADD_INLINE

    if old_finished:
        # still unimplemented
        return STATES.ADD_INLINE


def end_convo_wrapper(msg, update, context):
    """ Ends a conversation with text 'msg' """
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=msg)
    return ConversationHandler.END


def continue_convo_wrapper(movie_id: str, movie_idx: int, operation: str, update, context):
    query = update.callback_query
    query.answer()

    content = query.message.text.splitlines()
    content[movie_idx] = operation + endpoints.short_title(movie_id)
    text = "\n".join([f"{idx+1}: {line}" for idx, line in enumerate(content)])

    query.edit_message_text(text=text)
    return ConversationHandler.END


def _show_watch_list(update, context):
    chat_id = update.effective_chat["id"]
    return end_convo_wrapper(general.list_watchlist(chat_id), update, context)


def _show_watched(update, context):
    chat_id = update.effective_chat["id"]
    return end_convo_wrapper(general.list_watched(chat_id), update, context)


def _add_watch_list_inline(update, context):
    chat_id = update.effective_chat["id"]
    query = update.callback_query
    movie_id, movie_idx, *_ = query["message"]["reply_markup"]["inline_keyboard"][0][0]["callback_data"].split(SEP)[1:]

    # TODO - test
    # result_txt = general.add_watchlist(movie_id, chat_id)
    # deprecated_remove_watchlist(chat_id, movie_idx)
    return continue_convo_wrapper(movie_id, int(movie_idx), WATCH_LIST[0], update, context)


def _add_watched_inline(update, context):
    query = update.callback_query
    query.answer()
    return ConversationHandler.END


def skip(update, context):
    # retur
    query = update.callback_query
    query.answer()
    _, movie_idx, *_ = query["message"]["reply_markup"]["inline_keyboard"][0][0]["callback_data"].split(SEP)[1:]
    # return END for now, but we should actually return a buttn(?) with callback data of
    # movie_idx + 1
    # to signal search keyboard ctor to move to next movie to search
    return ConversationHandler.END


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
            CommandHandler("update", update_helper),
            MessageHandler(Filters.via_bot(username=set(["movie_list_bot"])), handle_movie)
        ],
        states={
            STATES.SHOW: [
                CallbackQueryHandler(_show_watch_list, pattern='^' + TWO + '$'),
                CallbackQueryHandler(_show_watched, pattern='^' + THREE + '$'),
                CallbackQueryHandler(end, pattern='^' + FOUR + '$'),
            ],
            STATES.ADD: [
                CallbackQueryHandler(_add_watch_list, pattern='^' + TWO + SEP),
                CallbackQueryHandler(_add_watched, pattern='^' + THREE + SEP),
                CallbackQueryHandler(end, pattern='^' + FOUR + '$'),
            ],
            STATES.ADD_INLINE: [
                CallbackQueryHandler(_add_watch_list_inline, pattern='^' + TWO + SEP),
                CallbackQueryHandler(_add_watched_inline, pattern='^' + THREE + SEP),
                CallbackQueryHandler(end, pattern='^' + FOUR + '$'),
                CallbackQueryHandler(skip, pattern='^' + FIVE + '$'),
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    return conv_handler
