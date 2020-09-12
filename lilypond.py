import os
import pathlib
import subprocess
from datetime import datetime
from typing import List
from telegram import Update
from telegram.ext import CallbackContext


def generate_filename(user: str):
    from constants import USER_FILES_DIR
    counter = 0
    while True:
        filename = datetime.utcnow().strftime("%y%m%d%H%M%S") + "-" + user + \
                   ("" if counter == 0 else f"-{str(counter)}")
        if any(filename in file for file in os.listdir(USER_FILES_DIR)):
            counter += 1
            continue
        else:
            return filename


def lilypond_compile(update: Update, context: CallbackContext):
    from constants import USER_FILES_DIR, LILY_VERSION, LILYSETTINGS_PATH

    text = update.inline_query.query if update.inline_query else update.message.text
    username = update.effective_user.username or str(update.effective_user.id)

    # where do we store the file
    pathlib.Path(USER_FILES_DIR).mkdir(parents=True, exist_ok=True)
    filename = generate_filename(username)
    src_file = f"{USER_FILES_DIR}/{filename}.ly"

    # write the file
    text = ("" if "\\version" in text else f'\\version "{LILY_VERSION}"'
            ) + f'\\include "{LILYSETTINGS_PATH}"\n{text}'
    with open(src_file, "w") as file:
        file.write(text)

    # compile
    try:
        # noinspection SpellCheckingInspection
        output, error = lilypond_process(
            ["-dbackend=eps", "-dresolution=300", "--png", "--loglevel=WARN", f"--output={USER_FILES_DIR}/", src_file])
    except Exception as exc:
        output = ""
        error = f"An error has occurred. Reporting to the dev...\n{type(exc).__name__}: {exc}"
        context.dispatcher.dispatch_error(update, exc)

    # prettify output
    error = error.replace(f"{os.getcwd()}/", "") \
        .replace(f"{USER_FILES_DIR}/", "") \
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
                             text=True, env={**os.environ, "LANG": "en"})
    return process.stdout, process.stderr
