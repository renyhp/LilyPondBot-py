from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
import time
from datetime import datetime

# noinspection SpellCheckingInspection
with open("debugtoken.txt", 'r') as token_file:
    token = token_file.read().strip()

counter = 0

def start(update, context):
    """Send a message when the command /start is issued."""
    global counter
    counter += 1
    update.message.reply_text('counter is now %d' % counter)


def log_things(context: CallbackContext):
    print("counter is %d" % counter, end='\r')


def main():
    # noinspection SpellCheckingInspection
    updater = Updater(token, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    job_queue: JobQueue = updater.job_queue
    job_queue.run_repeating(log_things, 1)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
