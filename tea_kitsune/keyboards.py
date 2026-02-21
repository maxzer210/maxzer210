from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu(is_admin: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🫖 Мой профиль"), KeyboardButton(text="🎁 Лояльность")],
        [KeyboardButton(text="📓 Чайный блокнот"), KeyboardButton(text="➕ Добавить заметку")],
        [KeyboardButton(text="🔳 Мой QR"), KeyboardButton(text="📣 Акции")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="✅ Отметить визит (админ)")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
