# -*- coding: utf-8 -*-

import logging.handlers
import os
import re
from datetime import datetime
from urllib.error import HTTPError

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from bot.core import add_user_if_new, add_wishlist_if_new, subscribe_wishlist, get_wishlist, get_product, \
    get_wishlist_count, get_product_count, get_wishlists_for_user, get_wl_url, get_p_url, get_products_for_user, \
    subscribe_product, add_product_if_new, update_entity_name, update_entity_price, get_entity_subscribers
from bot.user import User
from config import BOT_TOKEN
from database.db_wrapper import DBwrapper
from filters.own_filters import new_filter, show_filter
from geizhals.entity import EntityType
from geizhals.product import Product
from geizhals.wishlist import Wishlist
from userstate import UserState
from util.exceptions import AlreadySubscribedException, WishlistNotFoundException, ProductNotFoundException, \
    InvalidURLException
from util.formatter import bold, link, price

__author__ = 'Rico'

state_list = []
STATE_SEND_LINK = 0
STATE_SEND_WL_LINK = 1
STATE_SEND_P_LINK = 2

MAX_WISHLISTS = 5
MAX_PRODUCTS = 5

global logger
logdir_path = os.path.dirname(os.path.abspath(__file__))
logfile_path = os.path.join(logdir_path, "logs", "bot.log")

if not os.path.exists(os.path.join(logdir_path, "logs")):
    os.makedirs(os.path.join(logdir_path, "logs"))

logfile_handler = logging.handlers.WatchedFileHandler(logfile_path, 'a', 'utf-8')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[logfile_handler])

logger = logging.getLogger(__name__)

if not re.match("[0-9]+:[a-zA-Z0-9\-_]+", BOT_TOKEN):
    logging.error("Bot token not correct - please check.")
    exit(1)

updater = Updater(token=BOT_TOKEN)
dp = updater.dispatcher

cancel_button = InlineKeyboardButton("🚫 Abbrechen", callback_data='cancel')


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


# Text commands
def start_cmd(bot, update):
    """Bot start command"""
    user = update.message.from_user

    # If user is here for the first time > Save him to the DB
    add_user_if_new(User(user.id, user.first_name, user.username, user.language_code))

    keyboard = [[InlineKeyboardButton("Neuer Preisagent", callback_data="newPriceAgent"),
                 InlineKeyboardButton("Meine Preisagenten", callback_data="myPriceAgents")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.sendMessage(user.id, "Was möchtest du tun?", reply_markup=reply_markup)
    rm_state(user.id)


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


# Inline menus
def add_menu(bot, update):
    keyboard = [[InlineKeyboardButton("Wunschliste", callback_data='addWishlist'),
                 InlineKeyboardButton("Produkt", callback_data='addProduct')]]

    update.message.reply_text(
        "Wofür möchtest du einen Preisagenten einrichten?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_menu(bot, update):
    keyboard = [[InlineKeyboardButton("Wunschlisten", callback_data='showWishlists'),
                 InlineKeyboardButton("Produkte", callback_data='showProducts')]]

    update.message.reply_text(
        "Welche Preisagenten möchtest du einsehen?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def handle_text(bot, update):
    """Handles plain text sent to the bot"""
    user_id = update.message.from_user.id

    for userstate in state_list:
        if userstate.user_id() == user_id:
            if userstate.state() == STATE_SEND_P_LINK:
                add_product(bot, update)
            elif userstate.state() == STATE_SEND_WL_LINK:
                add_wishlist(bot, update)


def add_wishlist(bot, update):
    text = update.message.text
    user = update.message.from_user

    reply_markup = InlineKeyboardMarkup([[cancel_button]])

    add_user_if_new(user)

    try:
        url = get_wl_url(text)
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
                        text="Name oder Preis konnte nicht ausgelesen werden! Preisagent wurde nicht erstellt!")
    except Exception as e:
        logger.error(e)
        bot.sendMessage(chat_id=user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Preisagent wurde nicht erstellt!")
    else:
        add_wishlist_if_new(wishlist)

        try:
            logger.debug("Subscribing to wishlist.")
            subscribe_wishlist(user, wishlist)
            bot.sendMessage(user.id,
                            "Preisagent für die Wunschliste {link_name} erstellt! Aktueller Preis: {price}".format(
                                link_name=link(wishlist.url, wishlist.name),
                                price=bold(price(wishlist.price, signed=False))),
                            parse_mode="HTML",
                            disable_web_page_preview=True)
            rm_state(user.id)
        except AlreadySubscribedException as ase:
            logger.debug("User already subscribed!")
            bot.sendMessage(user.id,
                            "Du hast bereits einen Preisagenten für diese Wunschliste! Bitte sende mir eine andere URL.",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))


def add_product(bot, update):
    text = update.message.text
    user = update.message.from_user

    reply_markup = InlineKeyboardMarkup([[cancel_button]])

    add_user_if_new(user)

    try:
        url = get_p_url(text)
    except InvalidURLException:
        logger.debug("Invalid url '{}'!".format(text))
        bot.sendMessage(chat_id=user.id,
                        text="Die URL ist ungültig!",
                        reply_markup=reply_markup)
        return

    try:
        product = Product.from_url(url)
    except HTTPError as e:
        if e.code == 403:
            bot.sendMessage(chat_id=user.id, text="Das Produkt ist nicht zugänglich! Preisagent wurde nicht erstellt!")
    except ValueError as valueError:
        # Raised when price could not be parsed
        logger.error(valueError)
        bot.sendMessage(chat_id=user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Preisagent wurde nicht erstellt!")
    except Exception as e:
        logger.error(e)
        bot.sendMessage(chat_id=user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Wunschliste nicht erstellt!")
    else:
        add_product_if_new(product)

        try:
            logger.debug("Subscribing to product.")
            subscribe_product(user, product)
            bot.sendMessage(user.id,
                            "Preisagent für das Produkt {link_name} erstellt! Aktueller Preis: {price}".format(
                                link_name=link(product.url, product.name),
                                price=bold(price(product.price, signed=False))),
                            parse_mode="HTML",
                            disable_web_page_preview=True)
            rm_state(user.id)
        except AlreadySubscribedException as ase:
            logger.debug("User already subscribed!")
            bot.sendMessage(user.id,
                            "Du hast bereits einen Preisagenten für dieses Produkt! Bitte sende mir eine andere URL.",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))


# Method to check all wishlists for price updates
def check_for_price_update(bot, job):
    logger.debug("Checking for updates!")
    db = DBwrapper.get_instance()
    # TODO only get wishlists which have subscribers
    wishlists = db.get_all_wishlists()
    products = db.get_all_products()

    entities = wishlists + products

    # Check all entities for price updates
    for entity in entities:
        logger.debug("URL is '{}'".format(entity.url))
        old_price = entity.price
        old_name = entity.name
        try:
            new_price = entity.get_current_price()
            new_name = entity.get_current_name()
        except HTTPError as e:
            if e.code == 403:
                logger.error("Wunschliste ist nicht öffentlich!")

                if entity.TYPE == EntityType.PRODUCT:
                    product_hidden = "Das Produkt {link_name} ist leider nicht mehr einsehbar. " \
                                     "Ich entferne diesen Preisagenten!".format(link_name=link(entity.url, entity.name))
                    for user_id in db.get_users_for_product(entity.id):
                        bot.send_message(user_id, product_hidden, parse_mode="HTML")
                        db.unsubscribe_product(user_id, entity.id)
                    db.rm_product(entity.id)
                elif entity.TYPE == EntityType.WISHLIST:
                    wishlist_hidden = "Die Wunschliste {link_name} ist leider nicht mehr einsehbar. " \
                                      "Ich entferne diesen Preisagent.".format(link_name=link(entity.url, entity.name))
                    for user_id in db.get_users_for_wishlist(entity.id):
                        bot.send_message(user_id, wishlist_hidden, parse_mode="HTML")
                        db.unsubscribe_wishlist(user_id, entity.id)
                    db.rm_wishlist(entity.id)
        except ValueError as e:
            logger.error(e)
        except Exception as e:
            logger.error(e)
        else:
            if old_price != new_price:
                entity.price = new_price
                update_entity_price(entity, new_price)
                entity_subscribers = get_entity_subscribers(entity)

                for user_id in entity_subscribers:
                    # Notify each subscriber
                    notify_user(bot, user_id, entity, old_price)

            if old_name != new_name:
                update_entity_name(entity, new_name)


def get_inline_back_button(action):
    back_button = InlineKeyboardButton("↩️ Zurück", callback_data=action)
    return back_button


def get_delete_keyboard(entity_type, entity_id, back_action):
    back_button = InlineKeyboardButton("↩️ Zurück", callback_data=back_action)
    delete_button = InlineKeyboardButton("❌ Löschen", callback_data="delete_{entity_id}_{entity_type}".format(
        entity_type=entity_type.value, entity_id=entity_id))
    return InlineKeyboardMarkup([[delete_button], [back_button]])


def get_entity_keyboard(action, entities, prefix_text="", cancel=False, columns=2):
    """Returns a formatted inline keyboard for entity buttons"""
    buttons = []

    for entity in entities:
        callback_data = '{action}_{id}_{type}'.format(action=action, id=entity.id, type=entity.TYPE.value)
        button = InlineKeyboardButton(prefix_text + entity.name, callback_data=callback_data)
        buttons.append(button)

    return generate_keyboard(buttons, columns, cancel)


def generate_keyboard(buttons, columns, cancel=False):
    """Generate an inline keyboard with the specified amount of columns"""
    keyboard = []

    row = []
    for button in buttons:
        row.append(button)
        if len(row) >= columns:
            keyboard.append(row)
            row = []

    if len(row) > 0:
        keyboard.append(row)

    if cancel:
        keyboard.append([cancel_button])

    return InlineKeyboardMarkup(keyboard)


def notify_user(bot, user_id, entity, old_price):
    """Notify a user of price changes"""
    diff = entity.price - old_price

    if diff > 0:
        emoji = "📈"
        change = "teurer"
    else:
        emoji = "📉"
        change = "billiger"

    logger.info("Notifying user {}!".format(user_id))

    message = "Der Preis von {link_name} hat sich geändert: {price}\n\n" \
              "{emoji} {diff} {change}".format(link_name=link(entity.url, entity.name),
                                               price=bold(price(entity.price, signed=False)),
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
    if "_" in data:
        action, entity_id, entity_type_value = data.split("_")
        entity_type = EntityType(int(entity_type_value))
    else:
        action = data
        entity_id = None
        entity_type = None

    if entity_id:
        """Check if it's just a command or if an ID/type is passed"""
        if entity_type == EntityType.WISHLIST:
            wishlist_id = entity_id
            try:
                wishlist = get_wishlist(wishlist_id)
            except WishlistNotFoundException:
                invalid_wl_text = "Die Wunschliste existiert nicht!"
                bot.answerCallbackQuery(callback_query_id=callback_query_id, text=invalid_wl_text)
                bot.editMessageText(chat_id=user_id, message_id=message_id, text=invalid_wl_text)
                return

            if action == "delete":
                db.unsubscribe_wishlist(user_id, wishlist_id)

                keyboard = [
                    [InlineKeyboardButton("Rückgängig", callback_data='subscribe_{id}_wl'.format(id=wishlist_id))]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                bot.editMessageText(chat_id=user_id, message_id=message_id,
                                    text="Preisagent für die Wunschliste {link_name} wurde gelöscht!".format(
                                        link_name=link(wishlist.url, wishlist.name)),
                                    reply_markup=reply_markup,
                                    parse_mode="HTML", disable_web_page_preview=True)
                bot.answerCallbackQuery(callback_query_id=callback_query_id,
                                        text="Preisagent für die Wunschliste wurde gelöscht!")
            elif action == "show":
                bot.editMessageText(chat_id=user_id, message_id=message_id,
                                    text="Die Wunschliste {link_name} kostet aktuell {price}".format(
                                        link_name=link(wishlist.url, wishlist.name),
                                        price=bold(price(wishlist.price, signed=False))),
                                    reply_markup=get_delete_keyboard(EntityType.WISHLIST, wishlist.id, "showWishlists"),
                                    parse_mode="HTML", disable_web_page_preview=True)
                bot.answerCallbackQuery(callback_query_id=callback_query_id)
            elif action == "subscribe":
                db.subscribe_wishlist(wishlist_id, user_id)
                text = "Du hast die Wunschliste {link_name} erneut abboniert!".format(
                    link_name=link(wishlist.url, wishlist.name))
                bot.editMessageText(chat_id=user_id, message_id=message_id, text=text, parse_mode="HTML",
                                    disable_web_page_preview=True)
                bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Wunschliste erneut abboniert")
        elif entity_type == EntityType.PRODUCT:
            product_id = entity_id
            try:
                product = get_product(product_id)
            except ProductNotFoundException:
                invalid_p_text = "Das Produkt existiert nicht!"
                bot.answerCallbackQuery(callback_query_id=callback_query_id, text=invalid_p_text)
                bot.editMessageText(chat_id=user_id, message_id=message_id, text=invalid_p_text)
                return

            if action == "delete":
                pass
            elif action == "show":
                bot.editMessageText(chat_id=user_id, message_id=message_id,
                                    text="Das Produkt {link_name} kostet aktuell {price}".format(
                                        link_name=link(product.url, product.name),
                                        price=bold(price(product.price, signed=False))),
                                    reply_markup=get_delete_keyboard(EntityType.PRODUCT, product.id, "showProducts"),
                                    parse_mode="HTML", disable_web_page_preview=True)
                bot.answerCallbackQuery(callback_query_id=callback_query_id)
            elif action == "subscribe":
                # TODO implement
                pass
    elif action == "newPriceAgent":
        keyboard = [[InlineKeyboardButton("Wunschliste", callback_data='addWishlist'),
                     InlineKeyboardButton("Produkt", callback_data='addProduct')]]
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Wofür möchtest du einen Preisagenten einrichten?",
                            reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "myPriceAgents":
        keyboard = [[InlineKeyboardButton("Wunschlisten", callback_data='showWishlists'),
                     InlineKeyboardButton("Produkte", callback_data='showProducts')]]

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Welche Preisagenten möchtest du einsehen?",
                            reply_markup=InlineKeyboardMarkup(keyboard))
    elif action == "cancel":
        """Reset the user's state"""
        rm_state(user_id)
        text = "Okay, Ich habe die Aktion abgebrochen!"
        bot.editMessageText(chat_id=user_id, message_id=message_id, text=text)
        bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)
    elif action == "addWishlist":
        if get_wishlist_count(user_id) >= MAX_WISHLISTS:
            bot.editMessageText(chat_id=user_id, message_id=message_id,
                                text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                     "Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                                reply_markup=get_entity_keyboard("delete", get_wishlists_for_user(user_id),
                                                                 prefix_text="❌ ", cancel=True))
            return

        set_state(user_id, STATE_SEND_WL_LINK)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Bitte sende mir eine URL einer Wunschliste!",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))
        bot.answerCallbackQuery(callback_query_id=callback_query_id)
    elif action == "addProduct":
        if get_product_count(user_id) >= MAX_PRODUCTS:
            bot.editMessageText(chat_id=user_id, message_id=message_id,
                                text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                     "Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                                reply_markup=get_entity_keyboard("delete", get_products_for_user(user_id),
                                                                 prefix_text="❌ ", cancel=True))

            return
        set_state(user_id, STATE_SEND_P_LINK)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Bitte sende mir eine URL eines Produkts!",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))
        bot.answerCallbackQuery(callback_query_id=callback_query_id)
    elif action == "showWishlists":
        wishlists = get_wishlists_for_user(user_id)

        if len(wishlists) == 0:
            bot.editMessageText(chat_id=user_id, message_id=message_id,
                                text="Du hast noch keinen Preisagenten für eine Wunschliste angelegt!")
            return

        keyboard = get_entity_keyboard("show", wishlists)

        bot.answerCallbackQuery(callback_query_id=callback_query_id)
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Das sind deine Preisagenten für deine Wunschlisten:",
                            reply_markup=keyboard)
    elif action == "showProducts":
        products = get_products_for_user(user_id)

        if len(products) == 0:
            bot.editMessageText(chat_id=user_id, message_id=message_id,
                                text="Du hast noch keinen Preisagenten für ein Produkt angelegt!")
            return

        keyboard = get_entity_keyboard("show", products)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Das sind deine Preisagenten für deine Produkte:",
                            reply_markup=keyboard)


def unknown(bot, update):
    """Bot method which gets called when no command could be recognized"""
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
dp.add_handler(CommandHandler('start', callback=start_cmd))
dp.add_handler(CommandHandler(['help', 'hilfe'], callback=help_cmd))

# Bot specific commands
dp.add_handler(CommandHandler(['add', 'hinzufügen'], callback=add_menu))
dp.add_handler(CommandHandler("show", show_menu))

dp.add_handler(MessageHandler(new_filter, add_menu))
dp.add_handler(MessageHandler(show_filter, show_menu))

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
