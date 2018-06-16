# -*- coding: utf-8 -*-

import logging.handlers
import os
import re
from datetime import datetime
from urllib.error import HTTPError

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from bot.core import add_user_if_new, add_wishlist_if_new, subscribe_wishlist, get_wishlist, get_wishlist_count, get_wishlists_for_user, get_url
from bot.user import User
from config import BOT_TOKEN
from database.db_wrapper import DBwrapper
from filters.own_filters import delete_list_filter, my_lists_filter, new_list_filter
from geizhals.wishlist import Wishlist
from userstate import UserState
from util.exceptions import AlreadySubscribedException, WishlistNotFoundException, InvalidURLException, IncompleteRequestException
from util.formatter import bold, link, price

__author__ = 'Rico'

state_list = []
STATE_SEND_LINK = 0


global logger
logdir_path = os.path.dirname(os.path.abspath(__file__))
logfile_path = os.path.join(logdir_path, "logs", "bot.log")

if not os.path.exists(os.path.join(logdir_path, "logs")):
    os.makedirs(os.path.join(logdir_path, "logs"))

logfile_handler = logging.handlers.WatchedFileHandler(logfile_path, 'a', 'utf-8')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[logfile_handler, logging.StreamHandler()])

logger = logging.getLogger(__name__)

if not re.match("[0-9]+:[a-zA-Z0-9\-_]+", BOT_TOKEN):
    logging.error("Bot token not correct - please check.")
    exit(1)

updater = Updater(token=BOT_TOKEN)
dp = updater.dispatcher
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
    user = update.message.from_user

    # If user is here for the first time > Save him to the DB
    add_user_if_new(User(user.id, user.first_name, user.username, user.language_code))

    keyboard = [[KeyboardButton("Neue Liste"), KeyboardButton("Liste löschen")], [KeyboardButton("Meine Wunschlisten")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    bot.sendMessage(user.id, "Was möchtest du tun?", reply_markup=reply_markup)


def help_cmd(bot, update):
    """Bot help command"""
    user_id = update.message.from_user.id
    help_text = "Du brauchst Hilfe? Probiere folgende Befehle:\n\n" \
                "/start	-	Startmenü\n" \
                "/help	-	Zeigt diese Hilfe\n" \
                "/show  -   Zeigt deine Listen an\n" \
                "/add	-	Fügt neue Wunschliste hinzu\n" \
                "/remove	-	Entfernt eine Wunschliste\n"

    bot.sendMessage(user_id, help_text)


def add(bot, update):
    user = update.message.from_user

    if get_wishlist_count(user.id) < 4:
        add_wishlist(bot, update)
        return

    keyboard = [[InlineKeyboardButton("Liste auswählen", callback_data='removeMenu_-1')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.sendMessage(user.id,
                    "Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                    reply_markup=reply_markup)


# Sends the user a message with all his wishlists
def my_lists(bot, update):
    user_id = update.message.from_user.id
    wishlists = get_wishlists_for_user(user_id)

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

    wishlists = get_wishlists_for_user(user_id)

    if len(wishlists) == 0:
        bot.sendMessage(user_id, "Noch keine Wunschliste!")
        return

    keyboard = get_wishlist_keyboard("remove", wishlists)

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.sendMessage(user_id, "Bitte wähle die Wunschliste, die du löschen möchtest!", reply_markup=reply_markup)
    # TODO add button to cancel request


def handle_text(bot, update):
    """Handles plain text sent to the bot"""
    user_id = update.message.from_user.id

    for userstate in state_list:
        if userstate.user_id() == user_id and userstate.state() == STATE_SEND_LINK:
            add_wishlist(bot, update)
            rm_state(user_id)


def add_wishlist(bot, update):
    text = update.message.text
    user = update.message.from_user

    keyboard = [[InlineKeyboardButton("Abbrechen", callback_data='cancel_-1')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    add_user_if_new(user)

    try:
        url = get_url(text)
    except IncompleteRequestException:
        set_state(user.id, STATE_SEND_LINK)
        bot.sendMessage(chat_id=user.id,
                        text="Bitte sende mir eine URL einer Wunschliste!",
                        reply_markup=reply_markup)
        return
    except InvalidURLException:
        logger.debug("Invalid url '{}'!".format(text))
        bot.sendMessage(chat_id=user.id,
                        text="Die URL ist ungültig!",
                        reply_markup=reply_markup)
        return

    # Check if website is parsable!
    try:
        wishlist = Wishlist.from_url(url)
    except HTTPError as e:
        if e.code == 403:
            bot.sendMessage(chat_id=user.id, text="Wunschliste ist nicht öffentlich! Wunschliste nicht hinzugefügt!")
    except ValueError as valueError:
        # Raised when price could not be parsed
        logger.error(valueError)
        bot.sendMessage(chat_id=user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Wunschliste nicht hinzugefügt!")
    except Exception as e:
        logger.error(e)
        bot.sendMessage(chat_id=user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Wunschliste nicht hinzugefügt!")
    else:
        add_wishlist_if_new(wishlist)

        try:
            logger.debug("Subscribing to wishlist.")
            subscribe_wishlist(user, wishlist)
            bot.sendMessage(user.id,
                            "Wunschliste {link_name} abboniert! Aktueller Preis: {price}".format(
                                link_name=link(wishlist.url, wishlist.name),
                                price=bold(price(wishlist.price, signed=False))),
                            parse_mode="HTML",
                            disable_web_page_preview=True)
            rm_state(user.id)
        except AlreadySubscribedException as ase:
            logger.debug("User already subscribed!")
            bot.sendMessage(user.id, "Du hast diese Wunschliste bereits abboniert!")


# Method to check all wishlists for price updates
def check_for_price_update(bot, job):
    logger.debug("Checking for updates!")
    db = DBwrapper.get_instance()
    wishlists = db.get_all_wishlists()

    # Check all wishlists for price updates
    for wishlist in wishlists:
        logger.debug("URL is '{}'".format(wishlist.url))
        old_price = wishlist.price
        old_name = wishlist.name
        try:
            new_price = wishlist.get_current_price()
            new_name = wishlist.get_current_name()
        except HTTPError as e:
            if e.code == 403:
                logger.error("Wunschliste ist nicht öffentlich!")

                for user in db.get_users_for_wishlist(wishlist.id):
                    wishlist_hidden = "Die Wunschliste {link_name} ist leider nicht mehr einsehbar. " \
                                      "Ich entferne sie von deinen Wunschlisten.".format(link_name=link(wishlist.url, wishlist.name))
                    bot.send_message(user, wishlist_hidden, parse_mode="HTML")
                    db.unsubscribe_wishlist(user, wishlist.id)
                db.rm_wishlist(wishlist.id)
        except ValueError as e:
            logger.error(e)
        except Exception as e:
            logger.error(e)
        else:
            if old_price != new_price:
                wishlist.price = new_price
                db.update_wishlist_price(wishlist_id=wishlist.id, price=new_price)

                for user in db.get_users_for_wishlist(wishlist.id):
                    # Notify each user who subscribed to one wishlist
                    notify_user(bot, user, wishlist, old_price)

            if old_name != new_name:
                db.update_wishlist_name(wishlist.id, new_name)


def get_wishlist_keyboard(action, wishlists, columns=2):
    keyboard = []
    buttons = []

    for wishlist in wishlists:
        callback_data = '{action}_{id}'.format(action=action, id=wishlist.id)
        button = InlineKeyboardButton(wishlist.name, callback_data=callback_data)

        if len(buttons) >= columns:
            keyboard.append(buttons)
            buttons = []

        buttons.append(button)

    if len(buttons) > 0:
        keyboard.append(buttons)

    return keyboard


# Notify a user that his wishlist updated it's price
def notify_user(bot, user_id, wishlist, old_price):
    diff = wishlist.price - old_price

    if diff > 0:
        emoji = "📈"
        change = "teurer"
    else:
        emoji = "📉"
        change = "billiger"

    logger.info("Notifying user {}!".format(user_id))

    message = "Der Preis von {link_name} hat sich geändert: {price}\n\n" \
              "{emoji} {diff} {change}".format(link_name=link(wishlist.url, wishlist.name),
                                               price=bold(price(wishlist.price, signed=False)),
                                               emoji=emoji,
                                               diff=bold(price(diff)),
                                               change=change)
    bot.sendMessage(user_id, message, parse_mode="HTML", disable_web_page_preview=True)


# Handles the callbacks of inline keyboards
def callback_handler_f(bot, update):
    user_id = update.callback_query.from_user.id
    message_id = update.callback_query.message.message_id
    callback_query_id = update.callback_query.id

    db = DBwrapper.get_instance()

    data = update.callback_query.data
    action, wishlist_id = data.split("_")

    if wishlist_id != "-1" and not (action == "cancel" or action == "remvoveMenu"):
        try:
            wishlist = get_wishlist(wishlist_id)
        except WishlistNotFoundException:
            invalid_wl_text = "Die Wunschliste existiert nicht!"
            bot.answerCallbackQuery(callback_query_id=callback_query_id, text=invalid_wl_text)
            bot.editMessageText(chat_id=user_id, message_id=message_id, text=invalid_wl_text)
            return

    if action == "remove":
        db.unsubscribe_wishlist(user_id, wishlist_id)

        keyboard = [[InlineKeyboardButton("Rückgängig", callback_data='subscribe_{id}'.format(id=wishlist_id))]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Die Wunschliste {link_name} wurde gelöscht!".format(link_name=link(wishlist.url, wishlist.name)),
                            reply_markup=reply_markup,
                            parse_mode="HTML", disable_web_page_preview=True)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Die Wunschliste wurde gelöscht!")
    elif action == "show":
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Die Wunschliste {link_name} kostet aktuell {price}".format(
                                link_name=link(wishlist.url, wishlist.name), price=bold(price(wishlist.price))),
                            parse_mode="HTML", disable_web_page_preview=True)
    elif action == "subscribe":
        db.subscribe_wishlist(wishlist_id, user_id)
        text = "Du hast die Wunschliste {link_name} erneut abboniert!".format(link_name=link(wishlist.url, wishlist.name))
        bot.editMessageText(chat_id=user_id, message_id=message_id, text=text, parse_mode="HTML",
                            disable_web_page_preview=True)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Wunschliste erneut abboniert")
    elif action == "cancel":
        rm_state(user_id)
        text = "Okay, Ich habe die Aktion abgebrochen!"
        bot.editMessageText(chat_id=user_id, message_id=message_id, text=text)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)
    elif action == "removeMenu":
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                 "Entferne doch eine Wunschliste, die du nicht mehr benötigst.")
        bot.answerCallbackQuery(callback_query_id=callback_query_id,
                                text="Bitte lösche zuerst eine andere Wunschliste.")
        remove(bot, update)


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Sorry, den Befehl kenne ich nicht. Schau doch mal in der /hilfe")


def error_callback(bot, update, error):
    try:
        raise error
    except Unauthorized as e:
        logging.error(e.message)  # remove update.message.chat_id from conversation list
    except BadRequest as e:
        logging.error(e.message)  # handle malformed requests
    except TimedOut:
        pass  # connection issues are ignored for now
    except NetworkError as e:
        logging.error(e.message)  # handle other connection problems
    except ChatMigrated as e:
        logging.error(e.message)  # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError as e:
        logging.error(e.message)  # handle all other telegram related errors


# Basic handlers for standard commands
dp.add_handler(CommandHandler('start', callback=start))
dp.add_handler(CommandHandler(['help', 'hilfe'], callback=help_cmd))

# Bot specific commands
dp.add_handler(CommandHandler(['add', 'hinzufügen', 'new_list'], callback=add))
dp.add_handler(CommandHandler(['delete', 'remove', 'unsubscribe'], callback=remove))
dp.add_handler(CommandHandler(['my_lists', 'show'], my_lists))

dp.add_handler(MessageHandler(new_list_filter, add))
dp.add_handler(MessageHandler(delete_list_filter, remove))
dp.add_handler(MessageHandler(my_lists_filter, my_lists))

# Callback, Text and fallback handlers
dp.add_handler(CallbackQueryHandler(callback_handler_f))
dp.add_handler(MessageHandler(Filters.text, handle_text))
dp.add_handler(MessageHandler(Filters.command, unknown))
dp.add_error_handler(error_callback)

# Scheduling the check for updates
dt = datetime.today()
seconds = int(dt.timestamp())
repeat_in_minutes = 30
repeat_in_seconds = 60 * repeat_in_minutes
delta_t = repeat_in_seconds - (seconds % (60 * repeat_in_minutes))

updater.job_queue.run_repeating(callback=check_for_price_update, interval=repeat_in_seconds, first=delta_t)
updater.job_queue.start()

updater.start_polling()
logger.info("Bot started as @{}".format(updater.bot.username))
updater.idle()
