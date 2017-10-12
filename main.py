# -*- coding: utf-8 -*-

import logging

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from database.db_wrapper import DBwrapper
from wishlist import Wishlist
import re
from pyquery import PyQuery
import urllib
import socket
import sys


__author__ = 'Rico'

BOT_TOKEN = "<your_bot_token>"

state_list = []
STATE_SEND_LINK = 0

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher
tg_bot = updater.bot


def start(bot, update):
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    db = DBwrapper.get_instance()

    # If user is here for the first time > Save him to the DB
    if not db.is_user_saved(user_id):
        db.add_user(user_id, "en", first_name)
    # Otherwise ask him what he wants to do
    # 1) Add new wishlist
    # 2) Delete wishlist
    # 3) 
    pass


def delete(bot, update):
    # Ask user which wishlist he wants to delete
    remove(bot, update)


def add(bot, update):
    # TODO only allow up to 5 wishlists to check
def handle_text(bot, update):
    user_id = update.message.from_user.id

    for user in state_list:
        if user_id == user[0]:
            if user[1] == STATE_SEND_LINK:
                add_wishlist(bot, update)
                rm_state(user_id)


def add_wishlist(bot, update):
    text = update.message.text
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    pattern = "https:\/\/geizhals\.(de|at)\/\?cat=WL-([0-9]+)"
    db = DBwrapper.get_instance()
    url = ""

    if not re.match(pattern, text):
        if text == "/add":
            if not any(user_id in user for user in state_list):
                state_list.append([user_id, STATE_SEND_LINK])
            bot.sendMessage(chat_id=user_id, text="Please send me an url!")
            return
        elif "/add " in text:
            url = text.split()[1]
        else:
            logger.log(level=logging.DEBUG, msg="Invalid url '{}'!".format(text))
            bot.sendMessage(chat_id=user_id, text="The url is invalid!")
            return
    else:
        url = text


    if not db.is_user_saved(user_id):
        db.add_user(user_id, "en", first_name)

    id = int(re.search(pattern, text).group(2))

    # Check if website is parsable!
    try:
        logger.log(level=logging.DEBUG, msg="URL is '{}'".format(url))
        price = float(get_current_price(url))
        name = str(get_wishlist_name(url))
    except:
        bot.sendMessage(chat_id=user_id, text="Name or price cannot be obtained!")
        return

    url_in_list = False

    for element in db.get_wishlist_ids():
        if id == int(element[0]):
            url_in_list = True
            break

    if not url_in_list:
        logger.log(level=logging.DEBUG, msg="URL not in database!")
        db.add_wishlist(id, name, price, url)
    else:
        logger.log(level=logging.DEBUG, msg="URL in database!")

    user_subscribed = False

    for user in db.get_users_from_wishlist(id):
        if user_id == int(user):
            logger.log(level=logging.DEBUG, msg="User already subscribed!")
            bot.sendMessage(user_id, "Du hast diese Wunschliste bereits abboniert!")
            user_subscribed = True
            break

    if not user_subscribed:
        logger.log(level=logging.DEBUG, msg="Subscribing to wishlist.")
        bot.sendMessage(user_id, "Wunschliste abboniert!")
        db.subscribe_wishlist(id, user_id)


def remove(bot, update):
    user_id = update.message.from_user.id
    db = DBwrapper.get_instance()
    wishlists = db.get_wishlists_from_user(user_id)

    if len(wishlists) == 0:
        bot.sendMessage(user_id, "Noch keine Wunschliste!")
        return

    keyboard = []

    for wishlist in wishlists:
        button = [InlineKeyboardButton(wishlist.name(), callback_data='remove_{user_id}_{id}'.format(user_id=user_id, id=wishlist.id()))]
        keyboard.append(button)

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.sendMessage(user_id, "Bitte wähle die Wunschliste, die du löschen möchtest!", reply_markup=reply_markup)


    pass


# Method to check all wishlists for price updates
def check_for_price_update(bot, job):
    logger.log(level=logging.DEBUG, msg="Checking for updates!")
    db = DBwrapper.get_instance()
    wishlists = db.get_all_wishlists()

    for wishlist in wishlists:
        price = wishlist.price()
        new_price = get_current_price(wishlist.url())

        if price != new_price:
            wishlist.update_price(new_price)

            for user in db.get_users_from_wishlist(wishlist.id()):
                notify_user(bot, user, wishlist)


# Get the current price of a certain wishlist
def get_current_price(url):
    logger.log(level=logging.DEBUG, msg="Requesting url '{}'!".format(url))

    req = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    )

    f = urllib.request.urlopen(req)
    html = f.read().decode('utf-8')
    pq = PyQuery(html)

    price = pq('div.productlist__footer-cell span.gh_price').text()
    price = price[2:]  # Cut off the '€ ' before the real price
    price = price.replace(',', '.')

    # Parse price so that it's a proper comma value (no `,--`)
    pattern = "([0-9]+)\.([0-9]+|[-]+)"
    pattern_dash = "([0-9]+)\.([-]+)"

    if re.match(pattern, price):
        if re.match(pattern_dash, price):
            price = float(re.search(pattern_dash, price).group(1))
    else:
        raise ValueError("Couldn't parse price!")

    return float(price)


# Get the name of a wishlist
def get_wishlist_name(url):
    req = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    )

    f = urllib.request.urlopen(req)
    html = f.read().decode('utf-8')
    pq = PyQuery(html)
    name = pq('h1.gh_listtitle').text()
    return name


# Notify a user that his wishlist updated it's price
def notify_user(bot, user_id, wishlist):
    # TODO lang_id = language
    logger.log(level=logging.DEBUG, msg="Notifying user {}!".format(user_id))
    message = "Der Preis von [{name}]({url}) hat sich geändert: *{price} €*".format(name=wishlist.name(), url=wishlist.url(), price=wishlist.price())
    bot.sendMessage(user_id, message, parse_mode="Markdown", disable_web_page_preview=True)


# Handles the callbacks of inline keyboards
def callback_handler_f(bot, update):
    user_id = update.callback_query.from_user.id
    inline_message_id = update.callback_query.inline_message_id
    message_id = update.callback_query.message.message_id
    callback_query_id = update.callback_query.id

    db = DBwrapper.get_instance()

    data = update.callback_query.data
    action, chat_id, wishlist_id = data.split("_")

    if action == "remove":
        db.unsubscribe_wishlist(chat_id, wishlist_id)
        bot.editMessageText(chat_id=chat_id, message_id=message_id, text="Die Wunschliste wurde gelöscht!")
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Die Wunschliste wurde gelöscht!")

start_handler = CommandHandler('start', start)
delete_handler = CommandHandler('delete', delete)
add_handler = CommandHandler('add', add)
text_handler = MessageHandler(Filters.text, handle_text)
callback_handler = CallbackQueryHandler(callback_handler_f)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(delete_handler)
dispatcher.add_handler(add_handler)
dispatcher.add_handler(text_handler)
dispatcher.add_handler(callback_handler)

updater.start_polling()
