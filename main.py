# -*- coding: utf-8 -*-

import logging

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

__author__ = 'Rico'

BOT_TOKEN = "<your_bot_token>"

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher


def start(bot, update):
    pass


def delete(bot, update):
    pass


def add(bot, update):
    pass


start_handler = CommandHandler('start', start)
delete_handler = CommandHandler('delete', delete)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(delete_handler)
