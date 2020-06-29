import subprocess
from datetime import datetime, timezone

import lilypond

# noinspection SpellCheckingInspection
TOKEN_PATH = "debugtoken.txt"
LOG_PATH = "logs.txt"
RENYHP = 133748469

LILYSETTINGS_PATH = "lilysettings.ly"
USER_FILES_DIR = "user_files"

VERSION_NUMBER = "2.0.1"
COMMIT_HASH = subprocess.check_output(["git", "rev-parse", "--short", "origin/master"]).decode("utf-8")[:-1]
LILY_VERSION = lilypond.lilypond_process(["-v"])[0].split('\n', 1)[0][13:]

START_TIME = datetime.now(timezone.utc)
MONITOR = """\
LilyPondBot v{} @{}
GNU LilyPond {}

Start time: {}
Latest message received: {}
Messages received: {}
Commands processed: {}
Successful compilations: {}"""
