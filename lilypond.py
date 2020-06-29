import os
import pathlib
import subprocess
from datetime import datetime
from typing import List


def generate_filename(user: str):
    from constants import USER_FILES_DIR
    counter = 0
    while True:
        filename = user + "-" + datetime.utcnow().strftime("%y%m%d%H%M%S") + \
                   ("" if counter == 0 else f"-{str(counter)}")
        if any(filename in file for file in os.listdir(USER_FILES_DIR)):
            counter += 1
            continue
        else:
            return filename


def compile_text(text: str, username: str):
    from constants import USER_FILES_DIR, LILY_VERSION, LILYSETTINGS_PATH

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
    # noinspection SpellCheckingInspection
    output, error = lilypond_process(
        ["-dbackend=eps", "-dresolution=300", "--png", "--loglevel=WARN", f"--output={USER_FILES_DIR}/", src_file])

    # prettify output
    abs_path = str(pathlib.Path(src_file).absolute())
    error.replace(abs_path + ":", "")
    error.replace(abs_path, f"{filename}.ly")
    error.replace("\n\n", "\n")

    return filename, output, error


def add_padding(file_path):
    import cv2
    return cv2.imwrite(file_path,
                       cv2.copyMakeBorder(cv2.imread(file_path), 30, 30, 30, 30,
                                          cv2.BORDER_CONSTANT, value=[255, 255, 255]))


def lilypond_process(args: List[str]):
    args.insert(0, "lilypond")
    process = subprocess.run(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    return process.stdout, process.stderr
