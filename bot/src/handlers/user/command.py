import re

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Contact, ReplyKeyboardMarkup, KeyboardButton
from fluentogram import TranslatorRunner

from src.handlers.user.user_forms import RegisterForm, RequestForm
from src.utils.db import MongoDbClient
from src.utils.keyboards import create_inline_kb, create_reply_kb

router = Router()


@router.message(Command("start"))
async def start(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    user = await db.user.find_one({"id": message.from_user.id})
    if user is None:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Поділитись контактом",  request_contact=True)]], resize_keyboard=True, one_time_keyboard=True
        )
        await message.answer("Натисніть на кнопку для відправки номера телефону", reply_markup=kb)
    else:
        kb = create_reply_kb([[
            (locale.create_request()),
            (locale.user_requests())
        ]])
        await message.answer(locale.start(first_name=message.from_user.first_name), reply_markup=kb)


@router.message(lambda msg: msg.contact is not None)
async def get_contact(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    contact: Contact = message.contact
    await db.user.insert_one({
        "id": message.from_user.id,
        "phone": contact.phone_number,
        "name": contact.first_name,
    })
    await message.answer(f"Ваш номер {contact.phone_number} збережено ✅")
    kb = create_reply_kb([[
        (locale.create_request()),
        (locale.user_requests())
    ]])
    await message.answer(locale.start(first_name=message.from_user.first_name), reply_markup=kb)


@router.message(RequestForm.description)
async def process_description(message: Message, locale: TranslatorRunner, state: FSMContext):
    description = message.text.strip()
    kb = create_inline_kb([[
        (locale.confirm(), "confirm_description"),
        (locale.cancel(), "cancel_description")
    ]])
    await state.update_data(description=description)
    await message.answer(locale.is_correct_description(), reply_markup=kb)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_reply_btn(message: Message, locale: TranslatorRunner, db: MongoDbClient, state: FSMContext):
    text = message.text
    if text == locale.create_request():
        user = await db.user.find_one({"id": message.from_user.id})
        if not user:
            await message.answer(locale.unknown_user())
            return
        else:
            await message.answer(locale.describe_problem())
            await state.set_state(RequestForm.description)
    elif text == locale.user_requests():
        pass