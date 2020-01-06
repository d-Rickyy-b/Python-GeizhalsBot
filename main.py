# -*- coding: utf-8 -*-

import datetime
import logging.handlers
import os
from urllib.error import HTTPError

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

import config
from bot.core import *
from bot.menus.util import cancel_button, get_entities_keyboard, get_entity_keyboard
from bot.user import User
from geizhals import GeizhalsStateHandler
from util.exceptions import AlreadySubscribedException, WishlistNotFoundException, ProductNotFoundException, \
    InvalidURLException
from util.formatter import bold, link, price

__author__ = 'Rico'

STATE_SEND_LINK = 0
STATE_SEND_WL_LINK = 1
STATE_SEND_P_LINK = 2
STATE_IDLE = 3

project_path = os.path.dirname(os.path.abspath(__file__))
logdir_path = os.path.join(project_path, "logs")
logfile_path = os.path.join(logdir_path, "bot.log")

if not os.path.exists(logdir_path):
    os.makedirs(logdir_path)

logfile_handler = logging.handlers.WatchedFileHandler(logfile_path, 'a', 'utf-8')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, handlers=[logfile_handler])
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger("geizhals.main")

if not re.match(r"[0-9]+:[a-zA-Z0-9\-_]+", config.BOT_TOKEN):
    logging.error("Bot token not correct - please check.")
    exit(1)

updater = Updater(token=config.BOT_TOKEN, use_context=True)
dp = updater.dispatcher


# Text commands
def start_cmd(update, context):
    """Bot start command"""
    user = update.effective_user

    # If user is here for the first time > Save him to the DB
    add_user_if_new(User(user.id, user.first_name, user.username, user.language_code))
    context.bot.sendMessage(user.id, MainMenu.text, reply_markup=MainMenu.keyboard)
    context.user_data["state"] = STATE_IDLE


def help_cmd(update, context):
    """Bot help command"""
    user_id = update.effective_user.id
    help_text = "Du brauchst Hilfe? Probiere folgende Befehle:\n\n" \
                "/start	-	Startmenü\n" \
                "/help	-	Zeigt diese Hilfe\n" \
                "/show	-	Zeigt deine Listen an\n" \
                "/add	-	Fügt neue Wunschliste hinzu\n" \
                # "/remove	-	Entfernt eine Wunschliste\n"

    context.bot.sendMessage(user_id, help_text)


def broadcast(update, context):
    """Method to send a broadcast to all of the users of the bot"""
    user_id = update.effective_user.id
    bot = context.bot
    if user_id not in config.ADMIN_IDs:
        logger.warning("User {} tried to use the broadcast functionality!".format(user_id))
        return

    logging.info("Sending message broadcast to all users! Requested by admin '{}'".format(user_id))
    message_with_prefix = update.message.text
    final_message = message_with_prefix.replace("/broadcast ", "")
    users = get_all_subscribers()
    for user in users:
        bot.send_message(chat_id=user, text=final_message)

    for admin in config.ADMIN_IDs:
        bot.send_message(chat_id=admin, text="Sent message broadcast to all users! Requested by admin '{}' with the text:\n\n{}".format(user_id, final_message))


# Inline menus
def add_menu(update, _):
    """Send inline menu to add a new price agent"""
    update.message.reply_text(NewPriceAgentMenu.text, reply_markup=NewPriceAgentMenu.keyboard)


def show_menu(update, context):
    """Send inline menu to display all price agents"""
    update.message.reply_text(ShowPriceAgentsMenu.text, reply_markup=ShowPriceAgentsMenu.keyboard)


def delete_menu(update, context):
    # TODO When calling /remove the bot should open up a menu as well
    pass


def handle_text(update, context):
    """Handles plain text sent to the bot"""
    if context.user_data["state"]:
        if context.user_data["state"] == STATE_SEND_P_LINK:
            add_product(update, context)
        elif context.user_data["state"] == STATE_SEND_WL_LINK:
            add_wishlist(update, context)


def add_wishlist(update, context):
    text = update.message.text
    t_user = update.effective_user
    bot = context.bot

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
            context.user_data["state"] = STATE_IDLE
        except AlreadySubscribedException as ase:
            logger.debug("User already subscribed!")
            bot.sendMessage(t_user.id,
                            "Du hast bereits einen Preisagenten für diese Wunschliste! Bitte sende mir eine andere URL.",
                            reply_markup=InlineKeyboardMarkup([[cancel_button]]))


def add_product(update, context):
    msg = update.message
    text = update.message.text
    t_user = update.effective_user
    bot = context.bot

    logger.info("Adding new product for user '{}'".format(t_user.id))

    reply_markup = InlineKeyboardMarkup([[cancel_button]])
    user = User(t_user.id, t_user.first_name, t_user.username, t_user.language_code)
    add_user_if_new(user)

    try:
        url = get_p_url(text)
        logger.info("Valid URL for new product is '{}'".format(url))
    except InvalidURLException:
        logger.warning("Invalid url '{}' sent by user {}!".format(text, t_user))
        msg.reply_text(text="Die URL ist ungültig!", reply_markup=reply_markup)
        return

    try:
        product = Product.from_url(url)
    except HTTPError as e:
        logger.error(e)
        if e.code == 403:
            msg.reply_text(text="Das Produkt ist nicht zugänglich! Preisagent wurde nicht erstellt!")
        elif e.code == 429:
            msg.reply_text(text="Entschuldige, ich bin temporär bei Geizhals blockiert und kann keine Preise auslesen. Bitte probiere es später noch einmal.")
    except ValueError as valueError:
        # Raised when price could not be parsed
        logger.error(valueError)
        msg.reply_text(text="Name oder Preis konnte nicht ausgelesen werden! Preisagent wurde nicht erstellt!")
    except Exception as e:
        logger.error(e)
        msg.reply_text(text="Name oder Preis konnte nicht ausgelesen werden! Wunschliste nicht erstellt!")
    else:
        add_product_if_new(product)

        try:
            logger.debug("Subscribing to product.")
            subscribe_entity(user, product)
            msg.reply_text("Preisagent für das Produkt {link_name} erstellt! Aktueller Preis: {price}".format(
                                link_name=link(product.url, product.name),
                                price=bold(price(product.price, signed=False))),
                           parse_mode="HTML",
                           disable_web_page_preview=True)
            context.user_data["state"] = STATE_IDLE
        except AlreadySubscribedException:
            logger.debug("User already subscribed!")
            msg.reply_text("Du hast bereits einen Preisagenten für dieses Produkt! Bitte sende mir eine andere URL.",
                           reply_markup=InlineKeyboardMarkup([[cancel_button]]))


def check_for_price_update(context):
    """Check if the price of any subscribed wishlist or product was updated"""
    logger.debug("Checking for updates!")
    bot = context.bot

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


def show_pa_menu_handler(update, context):
    """Handles all the callbackquerys for the second menu (m2) - show price agents"""
    cbq = update.callback_query
    user_id = cbq.from_user.id
    menu, action = cbq.data.split("_")

    if action == "back":
        cbq.edit_message_text(text=MainMenu.text, reply_markup=MainMenu.keyboard)
    elif action == "showwishlists":
        wishlists = get_wishlists_for_user(user_id)

        if len(wishlists) == 0:
            cbq.edit_message_text(text="Du hast noch keinen Preisagenten für eine Wunschliste angelegt!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data="m00_showpriceagents")]]))
            return

        keyboard = get_entities_keyboard("show", wishlists)
        cbq.edit_message_text(text=ShowWLPriceAgentsMenu.text, reply_markup=keyboard)
    elif action == "showproducts":
        products = get_products_for_user(user_id)

        if len(products) == 0:
            cbq.edit_message_text(text="Du hast noch keinen Preisagenten für ein Produkt angelegt!",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data="m00_showpriceagents")]]))
            return

        keyboard = get_entities_keyboard("show", products)
        cbq.edit_message_text(text=ShowPPriceAgentsMenu.text, reply_markup=keyboard)
    else:
        logging.warning("A user tried to use an unimplemented method: '{}'".format(action))
        cbq.answer(text="Die gewählte Funktion ist noch nicht implementiert!")


def add_pa_menu_handler(update, context):
    """Handles all the callbackquerys for the third menu (m1) - add new price agent"""
    cbq = update.callback_query
    user_id = cbq.from_user.id
    menu, action = cbq.data.split("_")

    if action == "back":
        cbq.edit_message_text(text=MainMenu.text, reply_markup=MainMenu.keyboard)
    elif action == "addwishlist":
        if get_wishlist_count(user_id) >= config.MAX_WISHLISTS:
            keyboard = get_entities_keyboard("delete", get_wishlists_for_user(user_id), prefix_text="❌ ", cancel=True)
            cbq.edit_message_text(text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                       "Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                                  reply_markup=keyboard)
            return
        context.user_data["state"] = STATE_SEND_WL_LINK

        cbq.edit_message_text(text="Bitte sende mir eine URL einer Wunschliste!",
                              reply_markup=InlineKeyboardMarkup([[cancel_button]]))
        cbq.answer()
    elif action == "addproduct":
        if get_product_count(user_id) >= config.MAX_PRODUCTS:
            cbq.edit_message_text(text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                       "Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                                  reply_markup=get_entities_keyboard("delete", get_products_for_user(user_id),
                                                                     prefix_text="❌ ", cancel=True))

            return
        context.user_data["state"] = STATE_SEND_P_LINK

        cbq.edit_message_text(text="Bitte sende mir eine URL eines Produkts!",
                              reply_markup=InlineKeyboardMarkup([[cancel_button]]))
        cbq.answer()
    else:
        logging.warning("A user tried to use an unimplemented method: '{}'".format(action))
        cbq.answer(text="Die gewählte Funktion ist noch nicht implementiert!")


# Handles the callbacks of inline keyboards
def callback_handler_f(update, context):
    cbq = update.callback_query
    user_id = cbq.from_user.id
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
                cbq.answer(text=invalid_wl_text)
                cbq.edit_message_text(text=invalid_wl_text)
                return

            if action == "delete":
                unsubscribe_entity(user, wishlist)

                callback_data = 'subscribe_{id}_{type}'.format(id=wishlist_id,
                                                               type=EntityType.WISHLIST.value)

                keyboard = [
                    [InlineKeyboardButton("Rückgängig", callback_data=callback_data)]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                text = "Preisagent für die Wunschliste {0} wurde gelöscht!".format(link(wishlist.url, wishlist.name))
                cbq.edit_message_text(text=text,
                                      reply_markup=reply_markup,
                                      parse_mode="HTML", disable_web_page_preview=True)
                cbq.answer(text="Preisagent für die Wunschliste wurde gelöscht!")
            elif action == "show":
                cbq.edit_message_text(text="Die Wunschliste {link_name} kostet aktuell {price}".format(
                                        link_name=link(wishlist.url, wishlist.name),
                                        price=bold(price(wishlist.price, signed=False))),
                                      reply_markup=get_entity_keyboard(EntityType.WISHLIST, wishlist.entity_id),
                                      parse_mode="HTML", disable_web_page_preview=True)
                cbq.answer()
            elif action == "subscribe":
                try:
                    subscribe_entity(user, wishlist)
                    text = "Du hast die Wunschliste {link_name} erneut abboniert!".format(
                        link_name=link(wishlist.url, wishlist.name))
                    cbq.edit_message_text(text=text, parse_mode="HTML", disable_web_page_preview=True)
                    cbq.answer(text="Wunschliste erneut abboniert")
                except AlreadySubscribedException:
                    text = "Wunschliste bereits abboniert!"
                    cbq.edit_message_text(text=text, parse_mode="HTML", disable_web_page_preview=True)
                    cbq.answer(text=text)
            else:
                cbq.answer(text="Die gewählte Funktion ist noch nicht implementiert!")
        elif entity_type == EntityType.PRODUCT:
            product_id = entity_id
            try:
                product = get_product(product_id)
            except ProductNotFoundException:
                invalid_p_text = "Das Produkt existiert nicht!"
                cbq.answer(text=invalid_p_text)
                cbq.edit_message_text(text=invalid_p_text)
                return

            if action == "delete":
                print("Action delete executed")
                unsubscribe_entity(user, product)

                callback_data = 'subscribe_{id}_{type}'.format(id=product_id,
                                                               type=EntityType.PRODUCT.value)

                keyboard = [[InlineKeyboardButton("Rückgängig", callback_data=callback_data)]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                cbq.edit_message_text(text="Preisagent für das Produkt {link_name} wurde gelöscht!".format(
                                        link_name=link(product.url, product.name)),
                                    reply_markup=reply_markup,
                                    parse_mode="HTML", disable_web_page_preview=True)
                cbq.answer(text="Preisagent für das Produkt wurde gelöscht!")
            elif action == "show":
                cbq.edit_message_text(text="Das Produkt {link_name} kostet aktuell {price}".format(
                    link_name=link(product.url, product.name),
                    price=bold(price(product.price, signed=False))),
                    reply_markup=get_entity_keyboard(EntityType.PRODUCT, product.entity_id),
                    parse_mode="HTML", disable_web_page_preview=True)
                cbq.answer()
            elif action == "subscribe":
                try:
                    subscribe_entity(user, product)
                    text = "Du hast das Produkt {link_name} erneut abboniert!".format(
                        link_name=link(product.url, product.name))
                    cbq.edit_message_text(text=text, parse_mode="HTML", disable_web_page_preview=True)
                    cbq.answer(text="Produkt erneut abboniert")
                except AlreadySubscribedException:
                    text = "Produkt bereits abboniert!"
                    cbq.edit_message_text(text=text, parse_mode="HTML", disable_web_page_preview=True)
                    cbq.answer(text=text)
            elif action == "history":
                print("Action history executed")
                from geizhals.charts.dataset import Dataset
                items = get_price_history(product)
                ds = Dataset(product.name)
                for p, timestamp, name in items:
                    ds.add_price(price=p, timestamp=timestamp)
                chart = ds.get_chart()
                with open("test.png", "wb") as f:
                    f.write(chart)

                with open("test.png", "rb") as f:
                    cbq.message.reply_photo(photo=f)
            else:
                cbq.answer(text="Die gewählte Funktion ist noch nicht implementiert!")

    elif action == "cancel":
        """Reset the user's state"""
        context.user_data["state"] = STATE_IDLE
        text = "Okay, Ich habe die Aktion abgebrochen!"
        cbq.edit_message_text(text=text)
        cbq.answer(text=text)


def unknown(update, context):
    """Bot method which gets called when no command could be recognized"""
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Sorry, den Befehl kenne ich nicht. Schau doch mal in der /hilfe")


def error_callback(update, context):
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
dp.add_handler(CommandHandler("add", callback=add_menu))
dp.add_handler(CommandHandler("show", show_menu))

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
dt = datetime.datetime.today()
seconds = int(dt.timestamp())
repeat_in_minutes = 30
repeat_in_seconds = 60 * repeat_in_minutes
delta_t = repeat_in_seconds - (seconds % (60 * repeat_in_minutes))

updater.job_queue.run_repeating(callback=check_for_price_update, interval=repeat_in_seconds, first=delta_t)
updater.job_queue.start()

if config.USE_WEBHOOK:
    updater.start_webhook(listen="127.0.0.1", port=config.WEBHOOK_PORT, url_path=config.BOT_TOKEN, cert=config.CERTPATH, webhook_url=config.WEBHOOK_URL)
    updater.bot.set_webhook(config.WEBHOOK_URL)
else:
    updater.start_polling()

if config.USE_PROXIES:
    proxy_path = os.path.join(project_path, config.PROXY_LIST)
    with open(proxy_path, "r", encoding="utf-8") as f:
        proxies = f.read().split("\n")
        # Removing comments from the proxy list starting with a hash symbol and empty lines
        # Source: https://stackoverflow.com/questions/7058679/remove-all-list-elements-starting-with-a-hash
        proxies[:] = [x for x in proxies if not x.startswith('#') and not x == '']
    if proxies is not None and isinstance(proxies, list):
        logger.info("Using proxies!")
        gh = GeizhalsStateHandler(use_proxies=config.USE_PROXIES, proxies=proxies)
    else:
        logger.error("Proxies list is either empty or has mismatching type!")
else:
    GeizhalsStateHandler(use_proxies=config.USE_PROXIES, proxies=None)

logger.info("Bot started as @{}".format(updater.bot.username))
updater.idle()
