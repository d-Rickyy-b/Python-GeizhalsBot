from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .showpriceagentsmenu import ShowPriceAgentsMenu


class ShowWLPriceAgentsMenu(object):
    prev_menu = ShowPriceAgentsMenu
    text = "Das sind deine Preisagenten für deine Wunschlisten:"
    __keyboard_list = [[InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data='m03_back')]]
    keyboard = InlineKeyboardMarkup(__keyboard_list)
