import traceback
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue, Dispatcher, MessageHandler
from telegram.ext.filters import Filters

import monitor
import lilypond
from constants import *

# noinspection SpellCheckingInspection
with open(TOKEN_PATH, 'r') as token_file:
    token = token_file.read().strip()


def format_timedelta(td: timedelta):
    minutes, seconds = divmod(round(td.total_seconds(), 3), 60)
    return f"{int(minutes):02}:{round(seconds, 2):06.3f}"


def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    for i in range(0, len(s), n):
        yield s[i:i + n]


def start(update: Update, context):
    update.message.reply_text(
        f"Hello! Send me some LilyPond code{'in PM' if update.message.chat.type != 'private' else ''}, "
        "I will compile it for you and send you a picture with the sheet music.")


def help(update: Update, context):
    update.message.reply_html(
        f"Send me some LilyPond code{'in PM' if update.message.chat.type != 'private' else ''}, "
        "I will compile it for you and send you a picture with the sheet music."
        "\nFor now I can compile only little pieces of music, so the output of a big sheet music could be bad."
        "\n\n<b>What is LilyPond?</b>\n<i>LilyPond is a very powerful open-source music engraving program, "
        "which compiles text code to produce sheet music output. Full information:</i> lilypond.org"
        "\n\n<b>Feedback</b>"
        "\n<i>For any kind of feedback, you can freely message my dev at </i>@renyhp"
        "\n<i>Donations are welcome at </i>paypal.me/renyhp"
        "\n\n<b>Other commands:</b>"
        "\n/ping - Check response time\n/version - Get the running version", disable_web_page_preview=True)


def ping(update: Update, context):
    ping_time = datetime.now(timezone.utc) - update.message.date
    send_time = datetime.now(timezone.utc)
    message = update.message.reply_text(
        (monitor.get_monitor(context.bot.username) + "\n\n" if update.effective_user.id == RENYHP else "") +
        f"Time to receive your message: {format_timedelta(ping_time)}")
    ping_time = datetime.now(timezone.utc) - send_time
    message.edit_text(f"{message.text}\nTime to send this message: {format_timedelta(ping_time)}")


def version(update: Update, context):
    update.message.reply_html(
        f'LilyPondBot v{VERSION_NUMBER}-<code>{monitor.commit_hash}</code> '
        f'(<a href="https://github.com/renyhp/LilyPondBot-py/tree/{monitor.commit_hash}">source code</a>)\n'
        f'GNU LilyPond {monitor.lily_version}')


def log_error(update: Update, context: CallbackContext):  # maybe use package "logging"?
    error: TelegramError = context.error
    error_str = f"{datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S UTC')}" \
                f"\n{''.join(traceback.format_tb(error.__traceback__))}" \
                f"{type(error).__name__}: {error}"
    with open(LOG_PATH, 'a') as log_file:
        log_file.write("\n" + ("-" * 80) + "\n" + error_str + "\n\n")
    try:
        for chunk in chunks(error_str, 4000):
            context.bot.send_message(RENYHP, chunk)
    except:
        pass


def update_monitor(update: Update, context: CallbackContext):
    if update.effective_user.id != RENYHP:
        monitor.messages_received += 1
        if update.message.text.startswith("/"):
            monitor.commands_processed += 1


def main():
    # noinspection SpellCheckingInspection
    updater = Updater(token, use_context=True)

    dispatcher: Dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.all, update_monitor), group=0)
    for cmd, callback in (("start", start), ("help", help), ("ping", ping), ("version", version)):
        dispatcher.add_handler(CommandHandler(cmd, callback), group=1)
    dispatcher.add_handler(MessageHandler(~Filters.command, lilypond.quick_compile), group=1)
    dispatcher.add_error_handler(log_error)
    job_queue: JobQueue = updater.job_queue
    job_queue.run_repeating(monitor.program_monitor, 60, 0)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
