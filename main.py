import os
import pathlib
import traceback
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.error import TelegramError, NetworkError, BadRequest
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher, MessageHandler, \
    InlineQueryHandler, TypeHandler, DispatcherHandlerStop
from telegram.ext.filters import Filters

import constants
import monitor
from commands import start, help_, ping, version, send_compile_results, chunks, inspect_update


def log_error(update: Update, context: CallbackContext):  # maybe use package "logging"?
    error: TelegramError = context.error
    # ignore network errors and old inline queries
    if type(error) == NetworkError or \
            type(error) == BadRequest and error.message == "Query is too old and response timeout expired or query " \
                                                           "id is invalid":
        return
    error_str = f"{type(error).__name__}: {error}"
    if update and update.effective_user and update.effective_user.id != constants.RENYHP:
        try:
            if update.message is not None:
                update.message.reply_text(f"Oops! An error has occurred. Reporting to the dev..."
                                          f"\n\n{error_str}")
            elif update.inline_query is not None:
                update.inline_query.answer([InlineQueryResultArticle(uuid4(), "Oops!", InputTextMessageContent(
                    f"An error has occurred. Reporting to the dev...\n\n{error_str}"))])
        except TelegramError:
            pass
    full_error_str = f"{error_str}\n{''.join(traceback.format_tb(error.__traceback__))}"
    print("\n" + full_error_str + "\n\n")
    for chunk in chunks(full_error_str, 4000):
        try:
            context.bot.send_message(constants.RENYHP, chunk)
        except TelegramError:
            pass


def update_monitor(update: Update, context: CallbackContext):
    user_id = update.effective_user.id if update.effective_user is not None else update.effective_chat.id if update.effective_chat is not None else None
    if user_id != constants.RENYHP:
        monitor.user_ids.add(user_id)
        monitor.latest_message_time = datetime.now(timezone.utc)
        if update.message:
            monitor.messages_received += 1
            if update.message.text.startswith("/"):
                monitor.commands_processed += 1
        elif update.inline_query:
            monitor.inline_queries += 1


def anti_flood(update: Update, context: CallbackContext):
    if not update.effective_chat:
        return
    last_msg = context.chat_data.get("last_msg", None)
    now = datetime.now(timezone.utc)
    context.chat_data["last_msg"] = now
    if last_msg and last_msg + timedelta(seconds=1) > now:
        raise DispatcherHandlerStop()


def main():
    # noinspection SpellCheckingInspection
    updater = Updater(os.environ.get("LILYPONDBOT_TOKEN"), use_context=True)

    dispatcher: Dispatcher = updater.dispatcher
    dispatcher.add_handler(TypeHandler(Update, anti_flood), group=-1)
    dispatcher.add_handler(MessageHandler(Filters.text, update_monitor), group=0)
    dispatcher.add_handler(InlineQueryHandler(update_monitor), group=0)
    for cmd in (start, help_, ping, version):
        dispatcher.add_handler(CommandHandler(cmd.__name__.rstrip('_'), cmd, ~Filters.update.edited_message), group=1)
    dispatcher.add_handler(
        MessageHandler(~Filters.command & Filters.chat_type.private & Filters.text, send_compile_results),
        group=1)
    dispatcher.add_handler(InlineQueryHandler(send_compile_results), group=1)
    dispatcher.add_error_handler(log_error)
    pathlib.Path(constants.USER_FILES_DIR).mkdir(parents=True, exist_ok=True)
    pathlib.Path(constants.ERROR_FILES_DIR).mkdir(parents=True, exist_ok=True)
    updater.job_queue.run_repeating(monitor.cleanup, 30 * 60, 0)
    updater.start_polling(clean=True)
    print(f"Bot started! @{updater.bot.username}")
    updater.idle()


if __name__ == '__main__':
    main()
