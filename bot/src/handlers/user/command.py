import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from fluentogram import TranslatorRunner

from src.handlers.user.user_forms import RegisterForm, RequestForm
from src.utils.keyboards import create_inline_kb

router = Router()


@router.message(Command("start"))
async def start(message: Message, locale: TranslatorRunner):
    kb = create_inline_kb([[
        (locale.create_request(), "create_request"),
        (locale.status_request(), "status_request")
    ]])
    await message.answer(locale.start(first_name=message.from_user.first_name), reply_markup=kb)


@router.message(RegisterForm.name)
async def process_name(message: Message, locale: TranslatorRunner, state: FSMContext):
    name = message.text.strip()

    if not re.match(r"^[A-Za-zА-Яа-яҐґЄєІіЇї' -]+$", name):
        await message.answer(locale.incorrect_name())
    else:
        await state.update_data(name=name)
        kb = create_inline_kb([[
            (locale.confirm(), "confirm_name"),
            (locale.cancel(), "cancel_name")
        ]])
        await message.answer(locale.correct_name(name=name), reply_markup=kb)


@router.message(RequestForm.description)
async def process_description(message: Message, locale: TranslatorRunner, state: FSMContext):
    description = message.text.strip()
    kb = create_inline_kb([[
        (locale.confirm(), "confirm_description"),
        (locale.cancel(), "cancel_description")
    ]])
    await state.update_data(description=description)
    await message.answer(locale.is_correct_description(), reply_markup=kb)