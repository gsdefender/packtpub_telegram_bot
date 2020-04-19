#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# packtfree_telegram_bot - Receive Packt Publishing Ltd. Free Learning updates in Telegram each day
# Copyright (c) 2016-2020 Emanuele Cipolla <emanuele@emanuelecipolla.net>

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Usage:
Launch from shell.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram import ChatAction
from telegram.ext import Updater, CommandHandler, Job
import logging
from packtfree import get_book_info
import datetime
import pickle
import configparser
from functools import wraps

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

JOBS_PICKLE = 'job_tuples.pickle'
CONFIG_FILE = 'packtfree_telegram_bot.ini'

# WARNING: This information may change in future versions (changes are planned)
JOB_DATA = ('callback', 'interval', 'repeat', 'context', 'days', 'name', 'tzinfo')
JOB_STATE = ('_remove', '_enabled')


def load_jobs(jq):
    with open(JOBS_PICKLE, 'rb') as fp:
        while True:
            try:
                next_t, data, state = pickle.load(fp)
            except EOFError:
                break  # loaded all jobs

            # New object with the same data
            job = Job(**{var: val for var, val in zip(JOB_DATA, data)})

            # Restore the state it had
            for var, val in zip(JOB_STATE, state):
                attribute = getattr(job, var)
                getattr(attribute, 'set' if val else 'clear')()

            job.job_queue = jq

            jq._put(job, time_spec=next_t)


def save_jobs(jq):
    with jq._queue.mutex:  # in case job_queue makes a change

        if jq:
            job_tuples = jq._queue.queue
        else:
            job_tuples = []

        with open(JOBS_PICKLE, 'wb') as fp:
            for next_t, job in job_tuples:

                # This job is always created at the start
                if job.name == 'save_jobs_job' or job.name == 'force_update':
                    continue

                # Threading primitives are not pickleable
                data = tuple(getattr(job, var) for var in JOB_DATA)
                state = tuple(getattr(job, var).is_set() for var in JOB_STATE)

                # Pickle the job
                pickle.dump((next_t, data, state), fp)


def save_jobs_job(context):
    save_jobs(context.job_queue)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    update.message.reply_text(
        'Hi! Use /register to subscribe yourself to updates, or /get to immediately request information.')


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


def force_update(context=None):
    get_book_info(True)


@send_typing_action
def send_book_info(update, context):
    book_info = get_book_info()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id, photo=book_info['image'], caption=book_info['title'])
    context.bot.send_message(chat_id=chat_id, text=book_info['description'])


# when run in "alarm" mode, things change a little bit:
def send_book_info_alarm(bot, job):
    book_info = get_book_info()
    chat_id = job.context
    bot.send_photo(chat_id, photo=book_info['image'], caption=book_info['title'])
    bot.send_message(chat_id=chat_id, text=book_info['description'])


def register(update, context):
    """Adds a job to the queue"""
    chat_id = update.message.chat_id
    _token, _scraping_time, broadcast_time = read_config(CONFIG_FILE)

    # Add job to queue
    if 'job' not in context.chat_data:
        job = context.job_queue.run_daily(send_book_info_alarm, broadcast_time, context=chat_id)
        context.chat_data['job'] = job

        update.message.reply_text('Registration successfully completed.')
    else:
        update.message.reply_text('Already registered.')


def unregister(update, context):
    """Removes the job if the user changed their mind"""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have not registered yet.')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Registration successfully canceled.')


def error(update, context):
    logger.error('Update "%s" caused error "%s"', update, context.error)


def warn(update, context):
    logger.warning('Update "%s" caused warning "%s"', update, context.warning)


def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    if len(config) != 2:
        raise ValueError("Unable to load config file " + config_file)
    token = config['Bot']['token']
    autoupdate_hour = int(config['Bot']['autoupdate_hour'])
    autoupdate_min = int(config['Bot']['autoupdate_min'])
    autoupdate_sec = int(config['Bot']['autoupdate_sec'])
    today = datetime.date.today()
    scraping_time = datetime.time(hour=autoupdate_hour, minute=autoupdate_min, second=autoupdate_sec)
    broadcast_time = datetime.datetime.combine(today, scraping_time) + datetime.timedelta(hours=2)
    broadcast_time = broadcast_time.time()

    return (token, scraping_time, broadcast_time)


def main():
    token, scraping_time, _broadcast_time = read_config(CONFIG_FILE)
    updater = Updater(token, use_context=True)

    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("get", send_book_info))
    dp.add_handler(CommandHandler("register", register, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("unregister", unregister, pass_chat_data=True))

    # log all errors
    dp.add_error_handler(error)

    job_queue = updater.job_queue

    force_update()

    # First run
    job_queue.run_daily(force_update, scraping_time)
    # Periodically save jobs
    job_queue.run_repeating(save_jobs_job, datetime.timedelta(minutes=1))

    try:
        load_jobs(job_queue)
    except FileNotFoundError:
        pass

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    save_jobs(job_queue)


if __name__ == '__main__':
    main()
