from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .mainmenu import MainMenu


class ShowPriceAgentsMenu(object):
    prev_menu = MainMenu
    text = "Welche Preisagenten möchtest du einsehen?"
    __keyboard_list = [[InlineKeyboardButton("Wunschlisten", callback_data='m02_showwishlists'),
                        InlineKeyboardButton("Produkte", callback_data='m02_showproducts')],
                       [InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data='m02_back')]]
    keyboard = InlineKeyboardMarkup(__keyboard_list)
