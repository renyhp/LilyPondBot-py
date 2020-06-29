import glob
import os
from datetime import timedelta, datetime, timezone

from telegram import Update, ChatAction, Bot, TelegramError, InlineQueryResultArticle, InputTextMessageContent, \
    InlineQueryResultCachedPhoto, InlineQueryResultCachedDocument

from uuid import uuid4

import constants
import lilypond
import monitor
from constants import RENYHP, VERSION_NUMBER, USER_FILES_DIR, DEV_NULL


def format_timedelta(td: timedelta):
    minutes, seconds = divmod(round(td.total_seconds(), 3), 60)
    return f"{int(minutes):02}:{round(seconds, 2):06.3f}"


def start(update: Update, context):
    update.message.reply_text(
        f"Hello! Send me some LilyPond code{'in PM' if update.message.chat.type != 'private' else ''}, "
        "I will compile it for you and send you a picture with the sheet music.")


def secure_send(bot: Bot, chat_id, text: str, filename: str, is_inline_query: bool):
    if len(text) < 4000:
        if is_inline_query:
            return InlineQueryResultArticle(uuid4(), "Log", InputTextMessageContent(text))
        else:
            bot.send_message(chat_id, text)
    else:
        with open(filename, "w") as file:
            file.write(text)
        with open(filename, "rb") as file:
            document_message = bot.send_document(chat_id, file)
        if is_inline_query:
            return InlineQueryResultCachedDocument(uuid4(), "Log", document_message.document.file_id)


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


def send_compile_results(update: Update, context):
    # is this an inline query or text message
    is_inline_query = update.inline_query is not None
    if (is_inline_query and not update.inline_query.query) or (not is_inline_query and not update.message.text):
        return

    inline_query_results = []

    # typing...
    if not is_inline_query:
        update.effective_chat.send_action(ChatAction.TYPING)

    # compile
    filename, output, error = lilypond.lilypond_compile(
        update.inline_query.query if is_inline_query else update.message.text,
        update.effective_user.username or
        str(update.effective_user.id))

    # send text
    if is_inline_query:
        inline_query_results.append(
            InlineQueryResultArticle(uuid4(), "Source code", InputTextMessageContent(update.inline_query.query)))

    if error:
        result = secure_send(context.bot, DEV_NULL if is_inline_query else update.effective_chat.id, error,
                             f"{USER_FILES_DIR}/{filename}.log", is_inline_query)
        if result is not None:
            inline_query_results.append(result)

    if output:  # I want to know if that happens...
        error = f"ERROR\n\n{error}"
        output = f"OUTPUT\n\n{output}"
        secure_send(context.bot, RENYHP, error, f"{USER_FILES_DIR}/{filename}.error", False)
        secure_send(context.bot, RENYHP, output, f"{USER_FILES_DIR}/{filename}.output", False)

    successfully_compiled = False

    # send png's
    for png_file in glob.glob(f"{USER_FILES_DIR}/{filename}*.png"):
        successfully_compiled = True  # yay compiled
        if not is_inline_query:
            update.effective_chat.send_action(ChatAction.UPLOAD_PHOTO)
        lilypond.add_padding(png_file)
        if is_inline_query:
            with open(png_file, "rb") as file:
                file_id = context.bot.send_photo(DEV_NULL, file).photo[0].file_id
            inline_query_results.append(InlineQueryResultCachedPhoto(uuid4(), file_id))
        else:
            with open(png_file, "rb") as file:
                try:
                    update.message.reply_photo(file)
                except TelegramError:
                    update.message.reply_document(file)

    # send midi's
    for midi_file in glob.glob(f"{USER_FILES_DIR}/{filename}*.midi"):
        successfully_compiled = True
        if is_inline_query:
            with open(midi_file, "rb") as file:
                file_id = context.bot.send_document(DEV_NULL, file).document.file_id
            inline_query_results.append(InlineQueryResultCachedDocument(uuid4(), "MIDI output", file_id))
        else:
            update.effective_chat.send_action(ChatAction.UPLOAD_AUDIO)
            with open(midi_file, "rb") as file:
                update.message.reply_document(file)

    if is_inline_query:
        update.inline_query.answer(inline_query_results)

    if successfully_compiled and update.effective_user.id != RENYHP:
        monitor.successful_compilations += 1

    # clean up
    for filename in glob.glob(f"{USER_FILES_DIR}/{filename}*"):
        os.remove(filename)
