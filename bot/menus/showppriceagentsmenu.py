from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .showpriceagentsmenu import ShowPriceAgentsMenu


class ShowPPriceAgentsMenu(object):
    prev_menu = ShowPriceAgentsMenu
    text = "Das sind deine Preisagenten für deine Produkte:"
    __keyboard_list = [[InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data='m02_back')]]
    keyboard = InlineKeyboardMarkup(__keyboard_list)
