import os
from datetime import datetime, timezone

from telegram.ext import CallbackContext

import constants

latest_message_time = datetime.now(timezone.utc)
messages_received = 0
commands_processed = 0
successful_compilations = 0
inline_queries = 0
user_ids = set()


def get_monitor(bot_username):
    return constants.MONITOR.format(f"{constants.VERSION_NUMBER}-{constants.COMMIT_HASH}",
                                    bot_username,
                                    constants.LILY_VERSION,
                                    constants.START_TIME.strftime("%d/%m/%Y %H:%M:%S UTC"),
                                    latest_message_time.strftime("%d/%m/%Y %H:%M:%S UTC"),
                                    len(user_ids),
                                    messages_received,
                                    inline_queries,
                                    commands_processed,
                                    successful_compilations)


# not used anymore
def program_monitor(context: CallbackContext):
    os.system('cls' if os.name == 'nt' else 'clear') or None
    print(get_monitor(context.bot.username))
