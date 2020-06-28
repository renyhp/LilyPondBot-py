import subprocess
from typing import List

from telegram import Update
from telegram.ext import CallbackContext


def quick_compile(update: Update, context: CallbackContext):
    # TODO
    update.message.reply_text(update.message.text)


def lilypond_process(args: List[str]):
    args.insert(0, "lilypond")
    process = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    return tuple(x.decode('utf-8') for x in process.communicate())  # stdout, stderr
