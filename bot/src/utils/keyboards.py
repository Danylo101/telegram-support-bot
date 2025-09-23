from typing import List, Tuple

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_inline_kb(buttons: List[List[Tuple[str, str]]]) -> InlineKeyboardMarkup:
    """
    Повертає клавіатуру з кнопками.

    :param buttons: список рядків, кожен рядок — список кортежів (текст кнопки, callback_data)
    :return: InlineKeyboardMarkup
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=data) for text, data in row]
            for row in buttons
        ]
    )
    return keyboard