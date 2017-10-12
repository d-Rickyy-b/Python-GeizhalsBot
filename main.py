# -*- coding: utf-8 -*-

import logging

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from database.db_wrapper import DBwrapper
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
    pass


def add(bot, update):
    # TODO only allow up to 5 wishlists to check
    text = update.message.text
    url = text.split()[1]
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    pattern = "https:\/\/geizhals\.(de|at)\/\?cat=WL-([0-9]+)"
    db = DBwrapper.get_instance()

    if not re.match(pattern, url):
        if text.equals("/add"):
            if not any(user_id in user for user in state_list):
                state_list.append([user_id, STATE_SEND_LINK])
            bot.sendMessage(chat_id=user_id, text="Please send me an url!")
        else:
            bot.sendMessage(chat_id=user_id, text="The url is invalid!")
        return

    if not db.is_user_saved(user_id):
        db.add_user(user_id, "en", first_name)

    id = int(re.search(pattern, text).group(2))

    # Check if website is parsable!
    try:
        price = float(get_current_price(url))
        name = str(get_wishlist_name(url))
    except:
        bot.sendMessage(chat_id=user_id, text="Name or price cannot be obtained!")
        return

    print(db.get_wishlist_ids())

    url_in_list = False

    for element in db.get_wishlist_ids():
        if id == int(element[0]):
            url_in_list = True
            break

    if not url_in_list:
        logger.log(level=logging.DEBUG, msg="URL not in database!")
        db.add_wishlist(id, name, url, price)
    else:
        logger.log(level=logging.DEBUG, msg="URL in database!")

    user_subscribed = False

    for user in db.get_users_from_wishlist(id):
        if user_id == int(user[0]):
            logger.log(level=logging.DEBUG, msg="User already subscribed!")
            user_subscribed = True
            break

    if not user_subscribed:
        logger.log(level=logging.DEBUG, msg="Subscribing to wishlist.")
        db.subscribe_wishlist(id, user_id)


def check_for_price_update(url):
    # check for price update
    pass


def get_current_price(url):
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

    # Parse price so that it's a proper comma value (no `,--`)
    pattern = "([0-9]+),([0-9]+|[-]+)"
    pattern_dash = "([0-9]+),([-]+)"
    price = price[2:]  # Cut off the '€ ' before the real price

    if re.match(pattern, price):
        if re.match(pattern_dash, price):
            price = float(re.search(pattern_dash, price).group(1))
    else:
        raise ValueError("Couldn't parse price!")

    price_str = price + " €"
    print(price_str)

    # for user in db.get_users_from_wishlist()
    # notify_user(user_id)
    return price.replace(',', '.')


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
    name = pq('div h1.gh_listtitle').text()
    return name


def notify_user(bot, user_id, wishlist):
    message = "Der Preis von [{name}]({url}) hat sich geändert: *{price} €*".format(name=wishlist.name(), url=wishlist.url(), price=wishlist.price())
    # TODO lang_id = language
    bot.sendMessage(user_id, message, parse_mode="Markdown", disable_web_page_preview=True)
    raise NotImplementedError


start_handler = CommandHandler('start', start)
delete_handler = CommandHandler('delete', delete)
add_handler = CommandHandler('add', add)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(delete_handler)
dispatcher.add_handler(add_handler)


updater.start_polling()