from typing import List, Tuple

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


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


def create_reply_kb(buttons: List[List[str]]) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text) for text in row]
            for row in buttons
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard