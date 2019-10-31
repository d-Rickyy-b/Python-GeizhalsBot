from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .mainmenu import MainMenu


class NewPriceAgentMenu(object):
    prev_menu = MainMenu
    text = "Wofür möchtest du einen Preisagenten einrichten?"
    __keyboard_list = [[InlineKeyboardButton("Wunschliste", callback_data='m01_addwishlist'),
                        InlineKeyboardButton("Produkt", callback_data='m01_addproduct')],
                       [InlineKeyboardButton("↩️ Zurück", callback_data='m01_back')]]
    keyboard = InlineKeyboardMarkup(__keyboard_list)
