from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenu(object):
    prev_menu = None
    text = "Was möchtest du tun?"
    __keyboard_list = [[InlineKeyboardButton("Neuer Preisagent", callback_data="m00_newpriceagent"),
                        InlineKeyboardButton("Meine Preisagenten", callback_data="m00_showpriceagents")]]
    keyboard = InlineKeyboardMarkup(__keyboard_list)
