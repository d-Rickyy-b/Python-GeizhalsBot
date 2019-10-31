from telegram import InlineKeyboardButton, InlineKeyboardMarkup


cancel_button = InlineKeyboardButton("🚫 Abbrechen", callback_data='cancel')


def get_entity_keyboard(entity_type, entity_id, back_action):
    """Returns an action keyboard for a single entity"""
    back_button = InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data=back_action)
    delete_button = InlineKeyboardButton("❌ Löschen", callback_data="delete_{entity_id}_{entity_type}".format(
        entity_id=entity_id, entity_type=entity_type.value))
    history_button = InlineKeyboardButton("📊 Preisverlauf", callback_data="history_{entity_id}_{entity_type}".format(
        entity_id=entity_id, entity_type=entity_type.value))
    # TODO implement history button and functionality

    return InlineKeyboardMarkup([[delete_button, back_button], [history_button]])


def get_entities_keyboard(action, entities, prefix_text="", cancel=False, columns=2):
    """Returns a formatted inline keyboard for entity buttons"""
    buttons = []

    for entity in entities:
        callback_data = '{action}_{id}_{type}'.format(action=action, id=entity.entity_id, type=entity.TYPE.value)
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
