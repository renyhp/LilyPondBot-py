import os
import traceback
from datetime import datetime, timezone
from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.error import TelegramError, NetworkError
from telegram.ext import Updater, CommandHandler, CallbackContext, Dispatcher, MessageHandler, \
    InlineQueryHandler
from telegram.ext.filters import Filters

import constants
import monitor
from commands import start, help_, ping, version, send_compile_results


def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    for i in range(0, len(s), n):
        yield s[i:i + n]


def log_error(update: Update, context: CallbackContext):  # maybe use package "logging"?
    error: TelegramError = context.error
    if type(error) == NetworkError:
        return # ignore all network errors for now
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
    if update.effective_user.id != constants.RENYHP:
        monitor.user_ids.add(update.effective_user.id)
        monitor.latest_message_time = datetime.now(timezone.utc)
        if update.message:
            monitor.messages_received += 1
            if update.message.text.startswith("/"):
                monitor.commands_processed += 1
        elif update.inline_query:
            monitor.inline_queries += 1


def main():
    # noinspection SpellCheckingInspection
    updater = Updater(os.environ.get("LILYPONDBOT_TOKEN"), use_context=True)

    dispatcher: Dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text, update_monitor), group=0)
    dispatcher.add_handler(InlineQueryHandler(update_monitor), group=0)
    for cmd in (start, help_, ping, version):
        dispatcher.add_handler(CommandHandler(cmd.__name__.rstrip('_'), cmd), group=1)
    dispatcher.add_handler(MessageHandler(~Filters.command & Filters.private & Filters.text, send_compile_results),
                           group=1)
    dispatcher.add_handler(InlineQueryHandler(send_compile_results), group=1)
    dispatcher.add_error_handler(log_error)
    updater.job_queue.run_repeating(monitor.cleanup, 30 * 60, 0)
    updater.start_polling(clean=True)
    print(f"Bot started! @{updater.bot.username}")
    updater.idle()


if __name__ == '__main__':
    main()
