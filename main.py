# -*- coding: utf-8 -*-

import logging
import re
import urllib.request
from urllib.error import HTTPError
from datetime import datetime

from pyquery import PyQuery
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from config import BOT_TOKEN
from database.db_wrapper import DBwrapper
from filters.own_filters import OwnFilters
from userstate import UserState

__author__ = 'Rico'

state_list = []
STATE_SEND_LINK = 0

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher
useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) " \
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 " \
            "Safari/537.36"


def set_state(user_id, state):
    state_set = False

    for userstate in state_list:
        if userstate.user_id() == user_id:
            state_set = True
            break

    if not state_set:
        state_list.append(UserState(user_id, state))


def rm_state(user_id):
    index = 0
    for userstate in state_list:
        if userstate.user_id() == user_id:
            del state_list[index]
            break

        index += 1


def start(bot, update):
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    db = DBwrapper.get_instance()

    # If user is here for the first time > Save him to the DB
    if not db.is_user_saved(user_id):
        db.add_user(user_id, "en", first_name)

    # Otherwise ask him what he wants to do
    keyboard = [[KeyboardButton("Neue Liste"), KeyboardButton("Liste löschen")], [KeyboardButton("Meine Wunschlisten")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    bot.sendMessage(user_id, "Was möchtest du tun?", reply_markup=reply_markup)


def help(bot, update):
    user_id = update.message.from_user.id
    help_text = "Du brauchst Hilfe? Probiere folgende Befehle:\n\n" \
                "/start	-	Startmenü\n" \
                "/help	-	Zeigt diese Hilfe\n" \
                "/show  -   Zeigt deine Listen an\n" \
                "/add	-	Fügt neue Wunschliste hinzu\n" \
                "/remove	-	Entfernt eine Wunschliste\n"

    bot.sendMessage(user_id, help_text)


def delete(bot, update):
    # Ask user which wishlist he wants to delete
    remove(bot, update)


def add(bot, update):
    user_id = update.message.from_user.id
    db = DBwrapper.get_instance()
    if len(db.get_wishlists(user_id)) >= 5:
        keyboard = [[InlineKeyboardButton("Liste auswählen", callback_data='removeMenu_-1')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.sendMessage(user_id, "Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. Entferne doch eine Wunschliste, die du nicht mehr benötigst.", reply_markup=reply_markup)
    else:
        add_wishlist(bot, update)


# Sends the user a message with all his wishlists
def my_lists(bot, update):
    user_id = update.message.from_user.id
    db = DBwrapper.get_instance()
    wishlists = db.get_wishlists_from_user(user_id)

    if len(wishlists) == 0:
        bot.sendMessage(user_id, "Noch keine Wunschliste!")
        return

    keyboard = get_wishlist_keyboard("show", wishlists)

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.sendMessage(user_id, "Das sind deine Wunschlisten:", reply_markup=reply_markup)


# Remove a wishlist from a user's account
def remove(bot, update):
    try:
        user_id = update.message.from_user.id
    except AttributeError:
        user_id = update.callback_query.from_user.id

    db = DBwrapper.get_instance()
    wishlists = db.get_wishlists_from_user(user_id)

    if len(wishlists) == 0:
        bot.sendMessage(user_id, "Noch keine Wunschliste!")
        return

    keyboard = get_wishlist_keyboard("remove", wishlists)

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.sendMessage(user_id, "Bitte wähle die Wunschliste, die du löschen möchtest!", reply_markup=reply_markup)


# Process text sent to the bot (links)
def handle_text(bot, update):
    user_id = update.message.from_user.id

    for userstate in state_list:
        if userstate.user_id() == user_id:
            if userstate.state() == STATE_SEND_LINK:
                add_wishlist(bot, update)
                rm_state(user_id)


def add_wishlist(bot, update):
    text = update.message.text
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    pattern = "https:\/\/geizhals\.(de|at|eu)\/\?cat=WL-([0-9]+)"
    db = DBwrapper.get_instance()

    if not re.match(pattern, text):
        keyboard = [[InlineKeyboardButton("Abbrechen", callback_data='cancel_-1')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if text == "/add" or text == "Neue Liste":
            set_state(user_id, STATE_SEND_LINK)
            bot.sendMessage(chat_id=user_id, text="Bitte sende mir eine URL einer Wunschliste!", reply_markup=reply_markup)
            return
        elif "/add " in text:
            url = text.split()[1]
        else:
            bot.sendMessage(chat_id=user_id, text="Die URL ist ungültig!", reply_markup=reply_markup)
            logger.debug("Invalid url '{}'!".format(text))
            return
    else:
        url = text

    if not db.is_user_saved(user_id):
        db.add_user(user_id, "en", first_name)

    wishlist_id = int(re.search(pattern, text).group(2))

    # Check if website is parsable!
    try:
        logger.debug("URL is '{}'".format(url))
        price = float(get_current_price(url))
        name = str(get_wishlist_name(url))
    except HTTPError as e:
        if e.code == 403:
            bot.sendMessage(chat_id=user_id, text="Wunschliste ist nicht öffentlich! Wunschliste nicht hinzugefügt!")
        return
    except Exception as e:
        print(e)
        bot.sendMessage(chat_id=user_id, text="Name oder Preis konnte nicht ausgelesen werden! Wunschliste nicht hinzugefügt!")
        return

    if not db.is_wishlist_saved(wishlist_id):
        logger.debug("URL not in database!")
        db.add_wishlist(wishlist_id, name, price, url)
    else:
        logger.debug("URL in database!")

    if db.is_user_subscriber(user_id, wishlist_id):
        logger.debug("User already subscribed!")
        bot.sendMessage(user_id, "Du hast diese Wunschliste bereits abboniert!")
    else:
        bot.sendMessage(user_id, "Wunschliste [{name}]({url}) abboniert! Aktueller Preis: *{price:.2f} €*".format(name=name, url=url, price=price),
        logger.debug("Subscribing to wishlist.")
                        parse_mode="Markdown",
                        disable_web_page_preview=True)
        db.subscribe_wishlist(wishlist_id, user_id)
        rm_state(user_id)


# Method to check all wishlists for price updates
def check_for_price_update(bot, job):
    logger.debug("Checking for updates!")
    db = DBwrapper.get_instance()
    wishlists = db.get_all_wishlists()

    for wishlist in wishlists:
        old_price = wishlist.price()
        new_price = get_current_price(wishlist.url())

        if old_price != new_price:
            wishlist.update_price(new_price)
            db.update_price(wishlist_id=wishlist.id(), price=new_price)

            for user in db.get_users_from_wishlist(wishlist.id()):
                notify_user(bot, user, wishlist, old_price)


# Get the current price of a certain wishlist
def get_current_price(url):
    logger.debug("Requesting url '{}'!".format(url))

    req = urllib.request.Request(
        url,
        data=None,
        headers={'User-Agent': useragent}
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
        headers={'User-Agent': useragent}
    )

    f = urllib.request.urlopen(req)
    html = f.read().decode('utf-8')
    pq = PyQuery(html)
    name = pq('h1.gh_listtitle').text()
    return name


def get_wishlist_keyboard(action, wishlists):
    keyboard = []
    buttons = []

    for wishlist in wishlists:
        button = InlineKeyboardButton(wishlist.name(), callback_data='{action}_{id}'.format(action=action, id=wishlist.id()))

        if len(buttons) >= 2:
            keyboard.append(buttons)
            buttons = []

        buttons.append(button)

    if len(buttons) > 0:
        keyboard.append(buttons)

    return keyboard


# Notify a user that his wishlist updated it's price
def notify_user(bot, user_id, wishlist, old_price):
    # TODO lang_id = language
    diff = wishlist.price() - old_price

    if diff > 0:
        emoji = "📈"
        change = "teurer"
    else:
        emoji = "📉"
        change = "billiger"

    logger.debug("Notifying user {}!".format(user_id))
    message = "Der Preis von [{name}]({url}) hat sich geändert: *{price:.2f} €*\n\n" \
              "{emoji} *{diff:+.2f} €* {change}".format(name=wishlist.name(),
                                                        url=wishlist.url(),
                                                        price=wishlist.price(),
                                                        emoji=emoji,
                                                        diff=diff,
                                                        change=change)
    bot.sendMessage(user_id, message, parse_mode="Markdown", disable_web_page_preview=True)


# Handles the callbacks of inline keyboards
def callback_handler_f(bot, update):
    user_id = update.callback_query.from_user.id
    message_id = update.callback_query.message.message_id
    callback_query_id = update.callback_query.id

    db = DBwrapper.get_instance()

    data = update.callback_query.data
    action, wishlist_id = data.split("_")

    wishlist = db.get_wishlist_info(wishlist_id)

    if action == "remove":
        db.unsubscribe_wishlist(user_id, wishlist_id)

        keyboard = [[InlineKeyboardButton("Rückgängig", callback_data='subscribe_{id}'.format(id=wishlist_id))]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Die Wunschliste [{name}]({url}) wurde gelöscht!".format(name=wishlist.name(), url=wishlist.url()),
                            reply_markup=reply_markup,
                            parse_mode = "Markdown", disable_web_page_preview=True)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Die Wunschliste wurde gelöscht!")
    elif action == "show":
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Die Wunschliste [{name}]({url}) kostet aktuell *{price:.2f} €*".format(name=wishlist.name(), url=wishlist.url(), price=wishlist.price()),
                            parse_mode="Markdown", disable_web_page_preview=True)
    elif action == "subscribe":
        db.subscribe_wishlist(wishlist_id, user_id)
        text = "Du hast die Wunschliste [{name}]({url}) erneut abboniert!".format(name=wishlist.name(), url=wishlist.url())
        bot.editMessageText(chat_id=user_id, message_id=message_id, text=text, parse_mode="Markdown", disable_web_page_preview=True)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Wunschliste erneut abboniert")
    elif action == "cancel":
        rm_state(user_id)
        text = "Okay, Ich habe die Aktion abgebrochen!"
        bot.editMessageText(chat_id=user_id, message_id=message_id, text=text)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)
    elif action == "removeMenu":
        bot.editMessageText(chat_id=user_id, message_id=message_id, text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. Entferne doch eine Wunschliste, die du nicht mehr benötigst.")
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Bitte lösche zuerst eine andere Wunschliste.")
        remove(bot, update)


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, den Befehl kenne ich nicht. Schau doch mal in der /hilfe")


# Basic handlers for standard commands
start_handler = CommandHandler('start', callback=start)
help_handler = CommandHandler(['help', 'hilfe'], callback=help)

# Bot specific commands
new_list_handler = CommandHandler(['add', 'hinzufügen', 'new_list'], callback=add)
delete_handler = CommandHandler(['delete', 'remove', 'unsubscribe'], callback=delete)
show_list_handler = CommandHandler(['my_lists', 'show'], my_lists)

new_list_mhandler = MessageHandler(OwnFilters.new_list, add)
delete_mhandler = MessageHandler(OwnFilters.delete_list, delete)
show_list_mhandler = MessageHandler(OwnFilters.my_lists, my_lists)

# Callback, Text and fallback handlers
callback_handler = CallbackQueryHandler(callback_handler_f)
text_handler = MessageHandler(Filters.text, handle_text)
unknown_handler = MessageHandler(Filters.command, unknown)

# Adding the handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)

dispatcher.add_handler(new_list_handler)
dispatcher.add_handler(delete_handler)
dispatcher.add_handler(show_list_handler)
dispatcher.add_handler(new_list_mhandler)
dispatcher.add_handler(delete_mhandler)
dispatcher.add_handler(show_list_mhandler)

dispatcher.add_handler(callback_handler)
dispatcher.add_handler(text_handler)
dispatcher.add_handler(unknown_handler)

# Scheduling the check for updates
dt = datetime.today()
seconds = int(dt.timestamp())
delta_t = (60 * 30) - (seconds % (60 * 30))

updater.job_queue.run_repeating(callback=check_for_price_update, interval=60 * 30, first=delta_t)
updater.job_queue.start()

updater.start_polling()
