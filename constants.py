import subprocess
from datetime import datetime, timezone

import lilypond

# noinspection SpellCheckingInspection
RENYHP = 133748469
DEV_NULL = -1001483993984

LILYSETTINGS_PATH = "lilysettings.ly"
USER_FILES_DIR = "/tmp/LilyPondBot"
ERROR_FILES_DIR = "error_files"

VERSION_NUMBER = "2.1"
COMMIT_HASH = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8")[:-1]
LILY_VERSION = lilypond.lilypond_process(["-v"])[0].split('\n', 1)[0][13:]

START_TIME = datetime.now(timezone.utc)
MONITOR = """\
LilyPondBot v{} @{}
GNU LilyPond {}

Start time: {}
Latest message received: {}
Users seen in this session: {}
Messages received: {}
Inline queries received: {}
Commands processed: {}
Successful compilations: {}"""
