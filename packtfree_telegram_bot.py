#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# packtfree_telegram_bot - Receive Packt Publishing Ltd. Free Learning updates in Telegram each day
# Copyright (c) 2016 Emanuele Cipolla <emanuele@emanuelecipolla.net>

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

from telegram.ext import Updater, CommandHandler, Job
import logging
from packtfree import get_book_info
from datetime import datetime
import cPickle as pickle
import configparser

config_file = 'packtfree_telegram_bot.ini'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.DEBUG)

logger = logging.getLogger(__name__)

timers=dict()

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
	bot.sendMessage(update.message.chat_id, text='Hi! Use /register to subscribe yourself to updates, or /get to immediately request information.')

def send_book_info(bot, update_or_job):
    chat_id = ''
    book_info = get_book_info()

    if hasattr(update_or_job, 'context'):
		chat_id = update_or_job.context['chat_id'] 
    elif hasattr(update_or_job, 'message'):
		chat_id = update_or_job.message.chat_id
            	
    with open(book_info['image'], 'rb') as book_image:
	bot.sendPhoto(chat_id, photo=book_image)   
	bot.sendMessage(chat_id, text=book_info['title'])
	bot.sendMessage(chat_id, text=book_info['description'])

def alarm(bot, job):
	"""Function to send the alarm message"""
	send_book_info(bot,job)

def register(bot, update, args, job_queue):
	"""Adds a job to the queue"""
	chat_id = update.message.chat_id
	try:
		# Add job to queue
		job = Job(alarm, 86400, repeat=True, context=dict(chat_id=chat_id))
		timers[chat_id] = job
		job_queue.put(job)

		bot.sendMessage(chat_id, text='Registration successfully completed!')
	except (IndexError, ValueError):
		bot.sendMessage(chat_id, text='Simply type /register to be added into the queue')


def unregister(bot, update):
	"""Removes the job if the user changed their mind"""
	chat_id = update.message.chat_id

	if chat_id not in timers:
		bot.sendMessage(chat_id, text='You have not registered yet')
		return

	job = timers[chat_id]
	job.schedule_removal()
	del timers[chat_id]

	bot.sendMessage(chat_id, text='Registration successfully canceled!')


def warn(bot, update, warn):
	logger.warning('Update "%s" caused warning "%s"' % (update, warning))

def error(bot, update, error):
	logger.error('Update "%s" caused error "%s"' % (update, error))

def main():
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        token = config['Bot']['token']
    except AttributeError: # not python 3
        token = config.get('Bot','token')
    updater = Updater(token)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    	
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("get", send_book_info, pass_args=False, pass_job_queue=False))
    dp.add_handler(CommandHandler("register", register, pass_args=True, pass_job_queue=True))
    dp.add_handler(CommandHandler("unregister", unregister))

    # log all errors
    dp.add_error_handler(error)
	    
    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
	main()
