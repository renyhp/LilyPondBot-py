import glob
import os
from datetime import timedelta, datetime, timezone

from telegram import Update, ChatAction, Bot, TelegramError

import constants
import lilypond
import monitor
from constants import RENYHP, VERSION_NUMBER, USER_FILES_DIR


def format_timedelta(td: timedelta):
    minutes, seconds = divmod(round(td.total_seconds(), 3), 60)
    return f"{int(minutes):02}:{round(seconds, 2):06.3f}"


def start(update: Update, context):
    update.message.reply_text(
        f"Hello! Send me some LilyPond code{'in PM' if update.message.chat.type != 'private' else ''}, "
        "I will compile it for you and send you a picture with the sheet music.")


def secure_send(bot: Bot, chat_id, text: str, filename: str):
    if len(text) < 4000:
        bot.send_message(chat_id, text)
    else:
        with open(filename, "w") as file:
            file.write(text)
        with open(filename, "rb") as file:
            bot.send_document(chat_id, file)


def help_(update: Update, context):
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
        f'LilyPondBot v{VERSION_NUMBER}-<code>{constants.COMMIT_HASH}</code> '
        f'(<a href="https://github.com/renyhp/LilyPondBot-py/tree/{constants.COMMIT_HASH}">source code</a>)\n'
        f'GNU LilyPond {constants.LILY_VERSION}')


def compile_message(update: Update, context):
    # typing...
    update.effective_chat.send_action(ChatAction.TYPING)

    # compile
    filename, output, error = lilypond.compile_text(update.message.text,
                                                    update.effective_user.username or
                                                    str(update.effective_user.id))

    # send text
    if error:
        secure_send(context.bot, update.effective_chat.id, error, f"{USER_FILES_DIR}/{filename}.log")

    if output:  # I want to know if that happens...
        error = f"ERROR\n\n{error}"
        output = f"OUTPUT\n\n{output}"
        secure_send(context.bot, RENYHP, error, f"{USER_FILES_DIR}/{filename}.error")
        secure_send(context.bot, RENYHP, output, f"{USER_FILES_DIR}/{filename}.output")

    successfully_compiled = False

    # send png's
    for png_file in glob.glob(f"{USER_FILES_DIR}/{filename}*.png"):
        successfully_compiled = True # yay compiled
        update.effective_chat.send_action(ChatAction.UPLOAD_PHOTO)
        lilypond.add_padding(png_file)
        with open(png_file, "rb") as file:
            try:
                update.message.reply_photo(file)
            except TelegramError:
                update.message.reply_document(file)

    # send midi's
    for midi_file in glob.glob(f"{USER_FILES_DIR}/{filename}*.midi"):
        successfully_compiled = True
        update.effective_chat.send_action(ChatAction.UPLOAD_AUDIO)
        with open(midi_file, "rb") as file:
            update.message.reply_document(file)

    if successfully_compiled and update.effective_user.id != RENYHP:
        monitor.successful_compilations += 1

    # clean up
    for filename in glob.glob(f"{USER_FILES_DIR}/{filename}*"):
        os.remove(filename)


