from datetime import datetime, timezone
from telegram.ext import CallbackContext
import lilypond
import os
import subprocess
from constants import *

commit_hash = subprocess.check_output(["git", "rev-parse", "--short", "origin/master"]).decode("utf-8")[:-1]
start_time = datetime.now(timezone.utc)
latest_message_time = datetime.now(timezone.utc)
messages_received = 0
commands_processed = 0
successful_compilations = 0
lily_version = lilypond.lilypond_process(["-v"])[0].split('\n', 1)[0][13:]
MONITOR = """\
LilyPondBot v{} @{}
GNU LilyPond {}

Start time: {}
Latest message received: {}
Messages received: {}
Commands processed: {}
Successful compilations: {}"""


def get_monitor(bot_username):
    return MONITOR.format(f"{VERSION_NUMBER}-{commit_hash}",
                          bot_username,
                          lily_version,
                          start_time.strftime("%d/%m/%Y %H:%M:%S UTC"),
                          latest_message_time.strftime("%d/%m/%Y %H:%M:%S UTC"),
                          messages_received,
                          commands_processed,
                          successful_compilations)


def program_monitor(context: CallbackContext):
    os.system('cls' if os.name == 'nt' else 'clear') or None
    print(get_monitor(context.bot.username))
