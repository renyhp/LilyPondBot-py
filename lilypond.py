import os
import shutil
import subprocess
from datetime import datetime
from typing import List
import re

from telegram import Update
from telegram.ext import CallbackContext

import constants


def generate_filename(user: str):
    counter = 0
    while True:
        filename = datetime.utcnow().strftime("%y%m%d%H%M%S") + "-" + user + \
                   ("" if counter == 0 else f"-{str(counter)}")
        if any(filename in file for file in os.listdir(constants.USER_FILES_DIR)):
            counter += 1
            continue
        else:
            return filename


def lilypond_compile(update: Update, context: CallbackContext):
    text = update.inline_query.query if update.inline_query else update.effective_message.text
    username = update.effective_user.username or str(update.effective_user.id)

    # where do we store the file
    filename = generate_filename(username)
    src_file = f"{constants.USER_FILES_DIR}/{filename}.ly"

    # write the file
    text = f'\\include "{constants.LILYSETTINGS_PATH}"\n{text}'
    if "\\version" not in text:
        version = re.search(r"GNU LilyPond (\d+\.\d+\.\d+)", constants.LILY_VERSION).group(1)
        text = f'\\version "{version}"\n{text}'
    with open(src_file, "w") as file:
        file.write(text)

    # compile
    try:
        # noinspection SpellCheckingInspection
        output, error = lilypond_process(
            ["-dbackend=eps", "-dresolution=300", "--png", "--loglevel=WARN", f"--output={constants.USER_FILES_DIR}/",
             src_file])
    except Exception as exc:
        output = ""
        error = f"An error has occurred. Reporting to the dev...\n{type(exc).__name__}: {exc}"
        shutil.copy(src_file, f"{constants.ERROR_FILES_DIR}/{filename}.ly")
        context.dispatcher.dispatch_error(update, exc)

    # prettify output
    error = error.replace(f"{os.getcwd()}/", "") \
        .replace(f"{constants.USER_FILES_DIR}/", "") \
        .replace(f"{filename}.ly:", "") \
        .replace("\n\n", "\n")

    return filename, output, error


def add_padding(file_path):
    import cv2
    return cv2.imwrite(file_path,
                       cv2.copyMakeBorder(cv2.imread(file_path), 30, 30, 30, 30,
                                          cv2.BORDER_CONSTANT, value=[255, 255, 255]))


def lilypond_process(args: List[str]):
    args.insert(0, "lilypond")
    process = subprocess.run(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                             errors='replace', env={**os.environ, "LANG": "en"})
    return process.stdout, process.stderr
