from telegram import InlineKeyboardButton, InlineKeyboardMarkup


cancel_button = InlineKeyboardButton("🚫 Abbrechen", callback_data='cancel')


def get_entity_keyboard(entity_type, entity_id):
    """Returns an action keyboard for a single entity"""
    from geizhals.entities.entitytype import EntityType
    if entity_type == EntityType.WISHLIST:
        back_action = "m02_showwishlists"
    elif entity_type == EntityType.PRODUCT:
        back_action = "m02_showproducts"
    else:
        raise ValueError("Unknown EntityType")
    back_button = InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data=back_action)
    delete_button = InlineKeyboardButton("❌ Löschen", callback_data="m04_delete_{entity_id}_{entity_type}".format(
        entity_id=entity_id, entity_type=entity_type.value))
    history_button = InlineKeyboardButton("📊 Preisverlauf", callback_data="m04_history_{entity_id}_{entity_type}".format(
        entity_id=entity_id, entity_type=entity_type.value))

    return InlineKeyboardMarkup([[delete_button, history_button], [back_button]])


def get_entities_keyboard(action, entities, prefix_text="", cancel=False, columns=2):
    """Returns a formatted inline keyboard for entity buttons for the m03 menu"""
    buttons = []

    for entity in entities:
        callback_data = 'm04_{action}_{id}_{type}'.format(action=action, id=entity.entity_id, type=entity.TYPE.value)
        button = InlineKeyboardButton(prefix_text + entity.name, callback_data=callback_data)
        buttons.append(button)

    return generate_keyboard(buttons, columns, cancel, back_action="m00_showpriceagents")


def generate_keyboard(buttons, columns, cancel=False, back_action=None):
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

    if back_action:
        keyboard.append([InlineKeyboardButton("\U000021a9\U0000fe0f Zurück", callback_data=back_action)])

    return InlineKeyboardMarkup(keyboard)
