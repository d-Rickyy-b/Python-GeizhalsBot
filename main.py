# -*- coding: utf-8 -*-

import datetime
import logging.handlers
import os
import re
import io

from requests.exceptions import HTTPError
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

import bot.core as core
import config
from bot.menus import MainMenu, NewPriceAgentMenu, ShowPriceAgentsMenu, ShowWLPriceAgentsMenu, ShowPPriceAgentsMenu
from bot.menus.util import cancel_button, get_entities_keyboard, get_entity_keyboard
from bot.user import User
from geizhals import GeizhalsStateHandler
from geizhals.entities import EntityType, Wishlist, Product
from util.exceptions import AlreadySubscribedException, InvalidURLException
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
logging.getLogger("apscheduler").setLevel(logging.ERROR)

logger = logging.getLogger("geizhals.main")

if not re.match(r"[0-9]+:[a-zA-Z0-9\-_]+", config.BOT_TOKEN):
    logger.error("Bot token not correct - please check.")
    exit(1)

updater = Updater(token=config.BOT_TOKEN, use_context=True)
dp = updater.dispatcher


def admin_method(func):
    """Decorator for marking methods as admin-only methods, so that strangers can't use them"""

    def admin_check(update, context):
        user = update.effective_user

        if user.id in config.ADMIN_IDs:
            return func(update, context)

        update.message.reply_text('You have not the required permissions to do that!')
        logger.warning("User {} ({}, @{}) tried to use an admin function '{}'!".format(user.id, user.first_name, user.username,
                                                                                       func.__name__))

    return admin_check


# Text commands
def start_cmd(update, context):
    """Bot start command"""
    user = update.effective_user

    # If user is here for the first time > Save him to the DB
    u = User(user_id=user.id, first_name=user.first_name, last_name=user.last_name, username=user.username, lang_code=user.language_code)
    core.add_user_if_new(u)
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


@admin_method
def broadcast(update, context):
    """Method to send a broadcast to all of the users of the bot"""
    user_id = update.effective_user.id
    bot = context.bot

    message_with_prefix = update.message.text
    final_message = message_with_prefix.replace("/broadcast ", "")
    users = core.get_all_subscribers()
    logger.info("Sending message broadcast to all ({}) users! Requested by admin '{}'".format(len(users), user_id))
    for user in users:
        try:
            logger.debug("Sending broadcast to user '{}'".format(user))
            bot.send_message(chat_id=user, text=final_message)
        except Unauthorized:
            logger.info("User '{}' blocked the bot!".format(user))
            core.delete_user(user)

    for admin in config.ADMIN_IDs:
        bot.send_message(chat_id=admin,
                         text="Sent message broadcast to all users! Requested by admin '{}' with the text:\n\n{}".format(user_id, final_message))


@admin_method
def get_usage_info(update, context):
    subs = len(core.get_all_subscribers())
    products = len(core.get_all_products_with_subscribers())
    wishlists = len(core.get_all_wishlists_with_subscribers())
    all_subbed = len(core.get_all_entities_with_subscribers())
    all_entites = len(core.get_all_entities())
    price_count = core.get_price_count()
    total_users = len(core.get_all_users())
    update.message.reply_text("<b>Current statistics for</b> @{}\n\n"
                              "Subscriber count: {}\n\n"
                              "Subscribed products: {}\n"
                              "Subscribed wishlists: {}\n"
                              "<b>Subscribed entities total: {}</b>\n\n"
                              "Number of entities in db: {}\n\n"
                              "Number of stored prices in db: {}\n\n"
                              "Total users: {}"
                              "".format(context.bot.username, subs, products, wishlists, all_subbed, all_entites, price_count, total_users),
                              parse_mode="HTML")


# Inline menus
def add_menu(update, _):
    """Send inline menu to add a new price agent"""
    update.message.reply_text(NewPriceAgentMenu.text, reply_markup=NewPriceAgentMenu.keyboard)


def show_menu(update, _):
    """Send inline menu to display all price agents"""
    update.message.reply_text(ShowPriceAgentsMenu.text, reply_markup=ShowPriceAgentsMenu.keyboard)


def handle_text(update, context):
    """Handles plain text sent to the bot"""
    if context.user_data:
        if context.user_data["state"] == STATE_SEND_P_LINK:
            # add_product(update, context)
            add_entity(update, context)
        elif context.user_data["state"] == STATE_SEND_WL_LINK:
            # add_wishlist(update, context)
            add_entity(update, context)
    else:
        logger.info("User has no state but sent text!")


def add_entity(update, context):
    msg = update.message
    text = update.message.text
    t_user = update.effective_user

    logger.info("Adding new entity for user '{}'".format(t_user.id))

    reply_markup = InlineKeyboardMarkup([[cancel_button]])
    user = User(user_id=t_user.id, first_name=t_user.first_name, last_name=t_user.last_name, username=t_user.username, lang_code=t_user.language_code)
    core.add_user_if_new(user)

    try:
        entity_type = core.get_type_by_url(text)
        url = core.get_e_url(text, entity_type)
        logger.info("Valid URL for new entity is '{}'".format(url))
    except InvalidURLException:
        logger.warning("Invalid url '{}' sent by user {}!".format(text, t_user))
        msg.reply_text(text="Die URL ist ungültig!", reply_markup=reply_markup)
        return

    try:
        if entity_type == EntityType.WISHLIST:
            entity = Wishlist.from_url(url)
        elif entity_type == EntityType.PRODUCT:
            entity = Product.from_url(url)
        else:
            raise ValueError("EntityType '{}' not found!".format(entity_type))
    except HTTPError as e:
        logger.error(e)
        if e.response.status_code == 403:
            msg.reply_text(text="Die URL ist nicht öffentlich einsehbar, daher wurde kein neuer Preisagent erstellt!")
        elif e.response.status_code == 429:
            msg.reply_text(text="Entschuldige, ich bin temporär bei Geizhals blockiert und kann keine Preise auslesen. Bitte probiere es später noch einmal.")
    except (ValueError, Exception) as e:
        # Raised when price could not be parsed
        logger.error(e)
        msg.reply_text(text="Name oder Preis konnte nicht ausgelesen werden! Preisagent wurde nicht erstellt!")
    else:
        core.add_entity_if_new(entity)

        try:
            logger.debug("Subscribing to entity.")
            core.subscribe_entity(user, entity)
            entity_data = EntityType.get_type_article_name(entity_type)
            msg.reply_html("Preisagent für {article} {type} {link_name} erstellt! Aktueller Preis: {price}".format(
                                article=entity_data.get("article"),
                                type=entity_data.get("name"),
                                link_name=link(entity.url, entity.name),
                                price=bold(price(entity.price, signed=False))),
                           disable_web_page_preview=True)
            context.user_data["state"] = STATE_IDLE
        except AlreadySubscribedException:
            logger.debug("User already subscribed!")
            msg.reply_text("Du hast bereits einen Preisagenten für diese URL! Bitte sende mir eine andere URL.",
                           reply_markup=InlineKeyboardMarkup([[cancel_button]]))


def check_for_price_update(context):
    """Check if the price of any subscribed wishlist or product was updated"""
    bot = context.bot
    logger.debug("Checking for updates!")
    bot = context.bot

    entities = core.get_all_entities_with_subscribers()

    # Check all entities for price updates
    for entity in entities:
        logger.debug("URL is '{}'".format(entity.url))
        old_price = entity.price
        old_name = entity.name
        try:
            new_price = entity.get_current_price()
            new_name = entity.get_current_name()
        except HTTPError as e:
            if e.response.status_code == 403:
                logger.error("Entity is not public!")
                entity_type_data = EntityType.get_type_article_name(entity.TYPE)
                entity_hidden = "{article} {type} {link_name} ist leider nicht mehr einsehbar. " \
                                "Ich entferne diesen Preisagenten!".format(article=entity_type_data.get("article").capitalize(),
                                                                           type=entity_type_data.get("name"), link_name=link(entity.url, entity.name))

                for user_id in core.get_entity_subscribers(entity):
                    user = core.get_user_by_id(user_id)
                    bot.send_message(user_id, entity_hidden, parse_mode="HTML")
                    core.unsubscribe_entity(user, entity)

                core.rm_entity(entity)
        except (ValueError, Exception) as e:
            logger.error("Exception while checking for price updates! {}".format(e))
        else:
            if old_name != new_name:
                core.update_entity_name(entity, new_name)

            # Make sure to update the price no matter if it changed. Helps for generating charts
            entity.price = new_price
            core.update_entity_price(entity, new_price)

            if old_price == new_price:
                continue

            entity_subscribers = core.get_entity_subscribers(entity)

            for user_id in entity_subscribers:
                # Notify each subscriber
                try:
                    notify_user(bot, user_id, entity, old_price)
                except Unauthorized as e:
                    if e.message == "Forbidden: user is deactivated":
                        logger.info("Removing user from db, because account was deleted.")
                    elif e.message == "Forbidden: bot was blocked by the user":
                        logger.info("Removing user from db, because they blocked the bot.")
                    core.delete_user(user_id)


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


def entity_price_history(update, _):
    """Handles button clicks on the price history button"""
    cbq = update.callback_query
    data = cbq.data

    if "_" in data:
        menu, action, entity_id, entity_type_value = data.split("_")
        entity_type = EntityType(int(entity_type_value))
    else:
        logger.error("Error before unpacking. There is no '_' in the callback query data!")
        text = "An error occurred! This error was logged."
        cbq.message.reply_text(text=text, parse_mode="HTML", disable_web_page_preview=True)
        cbq.answer(text=text)
        return

    entity = core.get_entity(entity_id, entity_type)
    items = core.get_price_history(entity)

    from geizhals.charts.dataset import Dataset
    ds = Dataset(entity.name)
    for p, timestamp, name in items:
        ds.add_price(price=p, timestamp=timestamp)

    if len(items) <= 3 or len(ds.days) <= 3:
        cbq.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([]))
        cbq.message.reply_text("Entschuldige, leider habe ich nicht genügend Daten für diesen Preisagenten, um einen Preisverlauf anzeigen zu können! "
                               "Schau einfach in ein paar Tagen nochmal vorbei!")
        return

    chart = ds.get_chart()
    file_name = "{}.png".format(entity.entity_id)
    logger.info("Generated new chart '{}' for user '{}'".format(file_name, cbq.from_user.id))

    file = io.BytesIO(chart)
    cbq.message.reply_photo(photo=file)

    cbq.message.edit_text("Hier ist der Preisverlauf für {}".format(link(entity.url, entity.name)), reply_markup=InlineKeyboardMarkup([]),
                          parse_mode="HTML", disable_web_page_preview=True)
    cbq.answer()


def main_menu_handler(update, _):
    """Handles all the callbackquerys for the main/first menu (m0)"""
    cbq = update.callback_query
    menu, action = cbq.data.split("_")

    if action == "newpriceagent":
        cbq.edit_message_text(text=NewPriceAgentMenu.text,
                              reply_markup=NewPriceAgentMenu.keyboard)
    elif action == "showpriceagents":
        cbq.edit_message_text(text=ShowPriceAgentsMenu.text,
                              reply_markup=ShowPriceAgentsMenu.keyboard)
    else:
        logger.warning("A user tried to use an unimplemented method: '{}'".format(action))
        cbq.answer(text="Die gewählte Funktion ist noch nicht implementiert!")


def show_pa_menu_handler(update, _):
    """Handles all the callbackquerys for the second menu (m2) - show price agents"""
    cbq = update.callback_query
    user_id = cbq.from_user.id
    menu, action = cbq.data.split("_")

    if action == "back":
        cbq.edit_message_text(text=MainMenu.text, reply_markup=MainMenu.keyboard)
    elif action == "showwishlists":
        wishlists = core.get_wishlists_for_user(user_id)
        back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data="m00_showpriceagents")]])

        if len(wishlists) == 0:
            cbq.edit_message_text(text="Du hast noch keinen Preisagenten für eine Wunschliste angelegt!",
                                  reply_markup=back_keyboard)
            return

        keyboard = get_entities_keyboard("show", wishlists)
        cbq.edit_message_text(text=ShowWLPriceAgentsMenu.text, reply_markup=keyboard)
    elif action == "showproducts":
        products = core.get_products_for_user(user_id)

        if len(products) == 0:
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data="m00_showpriceagents")]])
            cbq.edit_message_text(text="Du hast noch keinen Preisagenten für ein Produkt angelegt!",
                                  reply_markup=back_keyboard)
            return

        keyboard = get_entities_keyboard("show", products)
        cbq.edit_message_text(text=ShowPPriceAgentsMenu.text, reply_markup=keyboard)
    else:
        logger.warning("A user tried to use an unimplemented method: '{}'".format(action))
        cbq.answer(text="Die gewählte Funktion ist noch nicht implementiert!")


def add_pa_menu_handler(update, context):
    """Handles all the callbackquerys for the third menu (m1) - add new price agent"""
    cbq = update.callback_query
    user_id = cbq.from_user.id
    menu, action = cbq.data.split("_")

    if action == "back":
        cbq.edit_message_text(text=MainMenu.text, reply_markup=MainMenu.keyboard)
    elif action == "addwishlist":
        if core.get_wishlist_count(user_id) >= config.MAX_WISHLISTS:
            keyboard = get_entities_keyboard("delete", core.get_wishlists_for_user(user_id), prefix_text="❌ ", cancel=True)
            cbq.edit_message_text(text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                       "Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                                  reply_markup=keyboard)
            return
        context.user_data["state"] = STATE_SEND_WL_LINK

        cbq.edit_message_text(text="Bitte sende mir eine URL einer Wunschliste!",
                              reply_markup=InlineKeyboardMarkup([[cancel_button]]))
        cbq.answer()
    elif action == "addproduct":
        if core.get_product_count(user_id) >= config.MAX_PRODUCTS:
            cbq.edit_message_text(text="Du kannst zu maximal 5 Wunschlisten Benachrichtigungen bekommen. "
                                       "Entferne doch eine Wunschliste, die du nicht mehr benötigst.",
                                  reply_markup=get_entities_keyboard("delete", core.get_products_for_user(user_id),
                                                                     prefix_text="❌ ", cancel=True))

            return
        context.user_data["state"] = STATE_SEND_P_LINK

        cbq.edit_message_text(text="Bitte sende mir eine URL eines Produkts!",
                              reply_markup=InlineKeyboardMarkup([[cancel_button]]))
        cbq.answer()
    else:
        logger.warning("A user tried to use an unimplemented method: '{}'".format(action))
        cbq.answer(text="Die gewählte Funktion ist noch nicht implementiert!")


def pa_detail_handler(update, context):
    """Handler for the price agent detail menu"""
    cbq = update.callback_query
    user_id = cbq.from_user.id
    menu, action, entity_id, entity_type_str = cbq.data.split("_")
    entity_type = EntityType(int(entity_type_str))

    entity = core.get_entity(entity_id, entity_type)
    user = core.get_user_by_id(user_id)

    if action == "show":
        cbq.edit_message_text(text="{link_name} kostet aktuell {price}".format(
            link_name=link(entity.url, entity.name),
            price=bold(price(entity.price, signed=False))),
            reply_markup=get_entity_keyboard(entity.TYPE, entity.entity_id),
            parse_mode="HTML", disable_web_page_preview=True)
        cbq.answer()
    elif action == "delete":
        core.unsubscribe_entity(user, entity)

        callback_data = 'm04_subscribe_{id}_{type}'.format(id=entity.entity_id,
                                                           type=entity.TYPE.value)
        keyboard = [[InlineKeyboardButton("Rückgängig", callback_data=callback_data)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "Preisagent für '{0}' wurde gelöscht!".format(link(entity.url, entity.name))

        cbq.edit_message_text(text=text,
                              reply_markup=reply_markup,
                              parse_mode="HTML", disable_web_page_preview=True)
        cbq.answer(text="Preisagent für wurde gelöscht!")
    elif action == "subscribe":
        entity_info = EntityType.get_type_article_name(entity.TYPE)
        try:
            core.subscribe_entity(user, entity)

            text = "Du hast {article} {entity_name} {link_name} erneut abboniert!".format(
                article=entity_info.get("article"), entity_name=entity_info.get("name"),
                link_name=link(entity.url, entity.name))
            cbq.edit_message_text(text=text, parse_mode="HTML", disable_web_page_preview=True)
            cbq.answer(text="{} erneut abboniert".format(entity_info.get("name")))
        except AlreadySubscribedException:
            text = "{} bereits abboniert!".format(entity_info.get("name"))
            cbq.edit_message_text(text=text, parse_mode="HTML", disable_web_page_preview=True)
            cbq.answer(text=text)
    elif action == "history":
        entity_price_history(update, context)
    else:
        logger.warning("A user tried to use an unimplemented method: '{}'".format(action))
        cbq.answer(text="Die gewählte Funktion ist noch nicht implementiert!")


def cancel_handler(update, context):
    """Handles clicks on the cancel button"""
    cbq = update.callback_query
    context.user_data["state"] = STATE_IDLE
    text = "Okay, Ich habe die Aktion abgebrochen!"
    cbq.edit_message_text(text=text)
    cbq.answer(text=text)


def callback_handler_f(update, _):
    """Handler for all the uncatched methods"""
    cbq = update.callback_query
    user_id = cbq.from_user.id

    logger.warning("The user '{}' used an undefined callback '{}'!".format(user_id, cbq.data))


def unknown(update, context):
    """Bot method which gets called when no command could be recognized"""
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="Sorry, den Befehl kenne ich nicht. Schau doch mal in der /hilfe")


def error_callback(_, context):
    error = context.error
    try:
        raise error
    except Unauthorized as e:
        logger.error(e.message)  # remove update.message.chat_id from conversation list
    except BadRequest as e:
        logger.error(e.message)  # handle malformed requests
    except TimedOut:
        pass  # connection issues are ignored for now
    except NetworkError as e:
        logger.error(e.message)  # handle other connection problems
    except ChatMigrated as e:
        logger.error(e.message)  # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError as e:
        logger.error(e.message)  # handle all other telegram related errors


dp.add_handler(CommandHandler("stats", callback=get_usage_info))
dp.add_handler(MessageHandler(Filters.regex("!stats"), callback=get_usage_info))

# Basic handlers for standard commands
dp.add_handler(CommandHandler("start", callback=start_cmd))
dp.add_handler(CommandHandler(["help", "hilfe"], callback=help_cmd))

# Bot specific commands
dp.add_handler(CommandHandler("add", callback=add_menu))
dp.add_handler(CommandHandler("show", callback=show_menu))
dp.add_handler(CommandHandler("broadcast", callback=broadcast))

# Callback, Text and fallback handlers
dp.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^m00_"))
dp.add_handler(CallbackQueryHandler(add_pa_menu_handler, pattern="^m01_"))
dp.add_handler(CallbackQueryHandler(show_pa_menu_handler, pattern="^m02_"))

dp.add_handler(CallbackQueryHandler(pa_detail_handler, pattern="^m04_"))
dp.add_handler(CallbackQueryHandler(entity_price_history, pattern="^m05_"))
dp.add_handler(CallbackQueryHandler(cancel_handler, pattern="^cancel$"))

dp.add_handler(CallbackQueryHandler(callback_handler_f))
dp.add_handler(MessageHandler(Filters.text, handle_text))
dp.add_handler(MessageHandler(Filters.command, unknown))
dp.add_error_handler(error_callback)

# Scheduling the check for updates
dt = datetime.datetime.today()
seconds = int(dt.timestamp())
repeat_in_minutes = 30
repeat_in_seconds = 60 * repeat_in_minutes
delta_t = repeat_in_seconds - (seconds % repeat_in_seconds)

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
        GeizhalsStateHandler(use_proxies=config.USE_PROXIES, proxies=proxies)
    else:
        logger.error("Proxies list is either empty or has mismatching type!")
        exit(1)
else:
    GeizhalsStateHandler(use_proxies=config.USE_PROXIES, proxies=None)

logger.info("Bot started as @{}".format(updater.bot.username))
updater.idle()
