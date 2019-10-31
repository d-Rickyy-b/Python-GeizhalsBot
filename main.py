# -*- coding: utf-8 -*-

import logging.handlers
import os
from datetime import datetime
from urllib.error import HTTPError

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from bot.core import *
from bot.menus.util import cancel_button, get_entities_keyboard, get_entity_keyboard
from bot.user import User
from config import BOT_TOKEN, USE_WEBHOOK, WEBHOOK_PORT, WEBHOOK_URL, CERTPATH, USE_PROXIES, PROXY_LIST, ADMIN_IDs
from filters.own_filters import new_filter, show_filter
from geizhals import GeizhalsStateHandler
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

project_path = os.path.dirname(os.path.abspath(__file__))
logfile_path = os.path.join(project_path, "logs", "bot.log")

if not os.path.exists(os.path.join(project_path, "logs")):
    os.makedirs(os.path.join(project_path, "logs"))

logfile_handler = logging.handlers.WatchedFileHandler(logfile_path, 'a', 'utf-8')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[logfile_handler])
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger("geizhals.main")

if not re.match(r"[0-9]+:[a-zA-Z0-9\-_]+", BOT_TOKEN):
    logging.error("Bot token not correct - please check.")
    exit(1)

updater = Updater(token=BOT_TOKEN)
dp = updater.dispatcher


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
    bot.sendMessage(user.id, MainMenu.text, reply_markup=MainMenu.keyboard)
    rm_state(user.id)


def help_cmd(bot, update):
    """Bot help command"""
    user_id = update.message.from_user.id
    help_text = "Du brauchst Hilfe? Probiere folgende Befehle:\n\n" \
                "/start	-	Startmenü\n" \
                "/help	-	Zeigt diese Hilfe\n" \
                "/show	-	Zeigt deine Listen an\n" \
                "/add	-	Fügt neue Wunschliste hinzu\n" \
                # "/remove	-	Entfernt eine Wunschliste\n"

    bot.sendMessage(user_id, help_text)


def broadcast(bot, update):
    """Method to send a broadcast to all of the users of the bot"""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDs:
        logger.warning("User {} tried to use the broadcast functionality!".format(user_id))
        return

    logging.info("Sending message broadcast to all users! Requested by admin '{}'".format(user_id))
    message_with_prefix = update.message.text
    final_message = message_with_prefix.replace("/broadcast ", "")
    users = get_all_subscribers()
    for user in users:
        bot.send_message(chat_id=user, text=final_message)

    for admin in ADMIN_IDs:
        bot.send_message(chat_id=admin, text="Sent message broadcast to all users! Requested by admin '{}' with the text:\n\n{}".format(user_id, final_message))


# Inline menus
def add_menu(bot, update):
    """Send inline menu to add a new price agent"""
    update.message.reply_text(NewPriceAgentMenu.text, reply_markup=NewPriceAgentMenu.keyboard)


def show_menu(bot, update):
    """Send inline menu to display all price agents"""
    update.message.reply_text(ShowPriceAgentsMenu.text, reply_markup=ShowPriceAgentsMenu.keyboard)


def delete_menu(bot, update):
    # TODO When calling /remove the bot should open up a menu as well
    pass


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
    t_user = update.message.from_user

    reply_markup = InlineKeyboardMarkup([[cancel_button]])
    user = User(t_user.id, t_user.first_name, t_user.username, t_user.language_code)
    add_user_if_new(user)

    try:
        url = get_wl_url(text)
    except InvalidURLException:
        logger.debug("Invalid url '{}'!".format(text))
        bot.sendMessage(chat_id=t_user.id,
                        text="Die URL ist ungültig!",
                        reply_markup=reply_markup)
        return

    # Check if website is parsable!
    try:
        wishlist = Wishlist.from_url(url)
    except HTTPError as e:
        logger.error(e)
        if e.code == 403:
            bot.sendMessage(chat_id=t_user.id, text="Wunschliste ist nicht öffentlich! Wunschliste nicht hinzugefügt!")
        elif e.code == 429:
            bot.sendMessage(chat_id=t_user.id, text="Entschuldige, ich bin temporär bei Geizhals blockiert und kann keine Preise auslesen. Bitte probiere es später noch einmal.")
    except ValueError as valueError:
        # Raised when price could not be parsed
        logger.error(valueError)
        bot.sendMessage(chat_id=t_user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Preisagent wurde nicht erstellt!")
    except Exception as e:
        logger.error(e)
        bot.sendMessage(chat_id=t_user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Preisagent wurde nicht erstellt!")
    else:
        add_wishlist_if_new(wishlist)

        try:
            logger.debug("Subscribing to wishlist.")
            subscribe_entity(user, wishlist)
            bot.sendMessage(t_user.id,
                            "Preisagent für die Wunschliste {link_name} erstellt! Aktueller Preis: {price}".format(
                                link_name=link(wishlist.url, wishlist.name),
                                price=bold(price(wishlist.price, signed=False))),
                            parse_mode="HTML",
                            disable_web_page_preview=True)
            rm_state(t_user.id)
        except AlreadySubscribedException as ase:
            logger.debug("User already subscribed!")
            bot.sendMessage(t_user.id,
                            "Du hast bereits einen Preisagenten für diese Wunschliste! Bitte sende mir eine andere URL.",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))


def add_product(bot, update):
    text = update.message.text
    t_user = update.message.from_user

    logger.info("Adding new product for user '{}'".format(t_user.id))

    reply_markup = InlineKeyboardMarkup([[cancel_button]])
    user = User(t_user.id, t_user.first_name, t_user.username, t_user.language_code)
    add_user_if_new(user)

    try:
        url = get_p_url(text)
        logger.info("Valid URL for new product is '{}'".format(url))
    except InvalidURLException:
        logger.warning("Invalid url '{}' sent by user {}!".format(text, t_user))
        bot.sendMessage(chat_id=t_user.id,
                        text="Die URL ist ungültig!",
                        reply_markup=reply_markup)
        return

    try:
        product = Product.from_url(url)
    except HTTPError as e:
        logger.error(e)
        if e.code == 403:
            bot.sendMessage(chat_id=t_user.id, text="Das Produkt ist nicht zugänglich! Preisagent wurde nicht erstellt!")
        elif e.code == 429:
            bot.sendMessage(chat_id=t_user.id, text="Entschuldige, ich bin temporär bei Geizhals blockiert und kann keine Preise auslesen. Bitte probiere es später noch einmal.")
    except ValueError as valueError:
        # Raised when price could not be parsed
        logger.error(valueError)
        bot.sendMessage(chat_id=t_user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Preisagent wurde nicht erstellt!")
    except Exception as e:
        logger.error(e)
        bot.sendMessage(chat_id=t_user.id,
                        text="Name oder Preis konnte nicht ausgelesen werden! Wunschliste nicht erstellt!")
    else:
        add_product_if_new(product)

        try:
            logger.debug("Subscribing to product.")
            subscribe_entity(user, product)
            bot.sendMessage(t_user.id,
                            "Preisagent für das Produkt {link_name} erstellt! Aktueller Preis: {price}".format(
                                link_name=link(product.url, product.name),
                                price=bold(price(product.price, signed=False))),
                            parse_mode="HTML",
                            disable_web_page_preview=True)
            rm_state(t_user.id)
        except AlreadySubscribedException:
            logger.debug("User already subscribed!")
            bot.sendMessage(t_user.id,
                            "Du hast bereits einen Preisagenten für dieses Produkt! Bitte sende mir eine andere URL.",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))


def check_for_price_update(bot, job):
    """Check if the price of any subscribed wishlist or product was updated"""
    logger.debug("Checking for updates!")

    entities = get_all_entities_with_subscribers()

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
                logger.error("Entity is not public!")

                if entity.TYPE == EntityType.PRODUCT:
                    entity_hidden = "Das Produkt {link_name} ist leider nicht mehr einsehbar. " \
                                    "Ich entferne diesen Preisagenten!".format(link_name=link(entity.url, entity.name))
                elif entity.TYPE == EntityType.WISHLIST:
                    entity_hidden = "Die Wunschliste {link_name} ist leider nicht mehr einsehbar. " \
                                    "Ich entferne diesen Preisagent.".format(link_name=link(entity.url, entity.name))
                else:
                    raise ValueError("No such entity type '{}'!".format(entity.TYPE))

                for user_id in get_entity_subscribers(entity):
                    user = get_user_by_id(user_id)
                    bot.send_message(user_id, entity_hidden, parse_mode="HTML")
                    unsubscribe_entity(user, entity)

                rm_entity(entity)
        except ValueError as e:
            logger.error("ValueError while checking for price updates! {}".format(e))
        except Exception as e:
            logger.error("Exception while checking for price updates! {}".format(e))
        else:
            if old_price != new_price:
                entity.price = new_price
                update_entity_price(entity, new_price)
                entity_subscribers = get_entity_subscribers(entity)

                for user_id in entity_subscribers:
                    # Notify each subscriber
                    try:
                        notify_user(bot, user_id, entity, old_price)
                    except Unauthorized as e:
                        if e.message == "Forbidden: user is deactivated":
                            logging.info("Removed user from db, because account was deleted.")
                            delete_user(user_id)

            if old_name != new_name:
                update_entity_name(entity, new_name)


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


def main_menu_handler(bot, update):
    """Handles all the callbackquerys for the main/first menu (m0)"""
    cbq = update.callback_query
    user_id = cbq.from_user.id
    message_id = cbq.message.message_id
    menu, action = cbq.data.split("_")

    if action == "newpriceagent":
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text=NewPriceAgentMenu.text,
                            reply_markup=NewPriceAgentMenu.keyboard)
    elif action == "showpriceagents":
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text=ShowPriceAgentsMenu.text,
                            reply_markup=ShowPriceAgentsMenu.keyboard)
    else:
        bot.answerCallbackQuery(callback_query_id=cbq.id, text="Die gewählte Funktion ist noch nicht implementiert!")


def show_pa_menu_handler(bot, update):
    """Handles all the callbackquerys for the second menu (m2)"""
    cbq = update.callback_query
    user_id = cbq.from_user.id
    message_id = cbq.message.message_id
    menu, action = cbq.data.split("_")

    if action == "back":
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text=MainMenu.text,
                            reply_markup=MainMenu.keyboard)
    elif action == "showwishlists":
        wishlists = get_wishlists_for_user(user_id)

        if len(wishlists) == 0:
            bot.editMessageText(chat_id=user_id, message_id=message_id,
                                text="Du hast noch keinen Preisagenten für eine Wunschliste angelegt!",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data="m00_showpriceagents")]]))
            return

        keyboard = get_entities_keyboard("show", wishlists)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text=ShowWLPriceAgentsMenu.text,
                            reply_markup=keyboard)
    elif action == "showproducts":
        products = get_products_for_user(user_id)

        if len(products) == 0:
            bot.editMessageText(chat_id=user_id, message_id=message_id,
                                text="Du hast noch keinen Preisagenten für ein Produkt angelegt!",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data="m00_showpriceagents")]]))
            return

        keyboard = get_entities_keyboard("show", products)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Das sind deine Preisagenten für deine Produkte:",
                            reply_markup=keyboard)
    else:
        bot.answerCallbackQuery(callback_query_id=cbq.id, text="Die gewählte Funktion ist noch nicht implementiert!")


def add_pa_menu_handler(bot, update):
    """Handles all the callbackquerys for the third menu (m1)"""
    cbq = update.callback_query
    user_id = cbq.from_user.id
    message_id = cbq.message.message_id
    menu, action = cbq.data.split("_")

    if action == "back":
        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text=MainMenu.text,
                            reply_markup=MainMenu.keyboard)
    elif action == "addwishlist":
        if get_wishlist_count(user_id) >= MAX_WISHLISTS:
            bot.editMessageText(chat_id=user_id, message_id=message_id,
                                text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                     "Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                                reply_markup=get_entities_keyboard("delete", get_wishlists_for_user(user_id),
                                                                   prefix_text="❌ ", cancel=True))
            return

        set_state(user_id, STATE_SEND_WL_LINK)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Bitte sende mir eine URL einer Wunschliste!",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))
        bot.answerCallbackQuery(callback_query_id=cbq.id)
    elif action == "addproduct":
        if get_product_count(user_id) >= MAX_PRODUCTS:
            bot.editMessageText(chat_id=user_id, message_id=message_id,
                                text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                     "Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                                reply_markup=get_entities_keyboard("delete", get_products_for_user(user_id),
                                                                   prefix_text="❌ ", cancel=True))

            return
        set_state(user_id, STATE_SEND_P_LINK)

        bot.editMessageText(chat_id=user_id, message_id=message_id,
                            text="Bitte sende mir eine URL eines Produkts!",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))
        bot.answerCallbackQuery(callback_query_id=cbq.id)
    else:
        bot.answerCallbackQuery(callback_query_id=cbq.id, text="Die gewählte Funktion ist noch nicht implementiert!")


# Handles the callbacks of inline keyboards
def callback_handler_f(bot, update):
    user_id = update.callback_query.from_user.id
    message_id = update.callback_query.message.message_id
    callback_query_id = update.callback_query.id
    user = get_user_by_id(user_id)

    if user is None:
        return

    data = update.callback_query.data
    if "_" in data:
        # TODO Input validation!
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
                unsubscribe_entity(user, wishlist)

                callback_data = 'subscribe_{id}_{type}'.format(id=wishlist_id,
                                                               type=EntityType.WISHLIST.value)

                keyboard = [
                    [InlineKeyboardButton("Rückgängig", callback_data=callback_data)]]
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
                                    reply_markup=get_entity_keyboard(EntityType.WISHLIST, wishlist.entity_id, "m02_showwishlists"),
                                    parse_mode="HTML", disable_web_page_preview=True)
                bot.answerCallbackQuery(callback_query_id=callback_query_id)
            elif action == "subscribe":
                try:
                    subscribe_entity(user, wishlist)
                    text = "Du hast die Wunschliste {link_name} erneut abboniert!".format(
                        link_name=link(wishlist.url, wishlist.name))
                    bot.editMessageText(chat_id=user_id, message_id=message_id, text=text, parse_mode="HTML",
                                        disable_web_page_preview=True)
                    bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Wunschliste erneut abboniert")
                except AlreadySubscribedException:
                    text = "Wunschliste bereits abboniert!"
                    bot.editMessageText(chat_id=user_id, message_id=message_id, text=text, parse_mode="HTML",
                                        disable_web_page_preview=True)
                    bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)
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
                unsubscribe_entity(user, product)

                callback_data = 'subscribe_{id}_{type}'.format(id=product_id,
                                                               type=EntityType.PRODUCT.value)

                keyboard = [[InlineKeyboardButton("Rückgängig", callback_data=callback_data)]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                bot.editMessageText(chat_id=user_id, message_id=message_id,
                                    text="Preisagent für das Produkt {link_name} wurde gelöscht!".format(
                                        link_name=link(product.url, product.name)),
                                    reply_markup=reply_markup,
                                    parse_mode="HTML", disable_web_page_preview=True)
                bot.answerCallbackQuery(callback_query_id=callback_query_id,
                                        text="Preisagent für das Produkt wurde gelöscht!")
            elif action == "show":
                bot.editMessageText(chat_id=user_id, message_id=message_id,
                                    text="Das Produkt {link_name} kostet aktuell {price}".format(
                                        link_name=link(product.url, product.name),
                                        price=bold(price(product.price, signed=False))),
                                    reply_markup=get_entity_keyboard(EntityType.PRODUCT, product.entity_id, "m02_showproducts"),
                                    parse_mode="HTML", disable_web_page_preview=True)
                bot.answerCallbackQuery(callback_query_id=callback_query_id)
            elif action == "subscribe":
                try:
                    subscribe_entity(user, product)
                    text = "Du hast das Produkt {link_name} erneut abboniert!".format(
                        link_name=link(product.url, product.name))
                    bot.editMessageText(chat_id=user_id, message_id=message_id, text=text, parse_mode="HTML",
                                        disable_web_page_preview=True)
                    bot.answerCallbackQuery(callback_query_id=callback_query_id, text="Produkt erneut abboniert")
                except AlreadySubscribedException:
                    text = "Produkt bereits abboniert!"
                    bot.editMessageText(chat_id=user_id, message_id=message_id, text=text, parse_mode="HTML",
                                        disable_web_page_preview=True)
                    bot.answerCallbackQuery(callback_query_id=callback_query_id, text=text)
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

dp.add_handler(CommandHandler('broadcast', callback=broadcast))

# Callback, Text and fallback handlers
dp.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^m00_"))
dp.add_handler(CallbackQueryHandler(add_pa_menu_handler, pattern="^m01_"))
dp.add_handler(CallbackQueryHandler(show_pa_menu_handler, pattern="^m02_"))

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

if USE_WEBHOOK:
    updater.start_webhook(listen="127.0.0.1", port=WEBHOOK_PORT, url_path=BOT_TOKEN, cert=CERTPATH, webhook_url=WEBHOOK_URL)
    updater.bot.set_webhook(WEBHOOK_URL)
else:
    updater.start_polling()

if USE_PROXIES:
    proxy_path = os.path.join(project_path, PROXY_LIST)
    with open(proxy_path, "r", encoding="utf-8") as f:
        proxies = f.read().split("\n")
        # Removing comments from the proxy list starting with a hash symbol and empty lines
        # Source: https://stackoverflow.com/questions/7058679/remove-all-list-elements-starting-with-a-hash
        proxies[:] = [x for x in proxies if not x.startswith('#') and not x == '']
    if proxies is not None and isinstance(proxies, list):
        logger.info("Using proxies!")
        gh = GeizhalsStateHandler(use_proxies=USE_PROXIES, proxies=proxies)
    else:
        logger.error("Proxies list is either empty or has mismatching type!")
else:
    GeizhalsStateHandler(use_proxies=USE_PROXIES, proxies=None)

logger.info("Bot started as @{}".format(updater.bot.username))
updater.idle()
