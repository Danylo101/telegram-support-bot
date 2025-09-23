from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from fluentogram import TranslatorRunner

from src.utils.db import MongoDbClient
from src.utils.keyboards import create_inline_kb
from src.utils.permissions import operator_required

router = Router()

@router.message(Command("status"))
@operator_required
async def status(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    # data = await db.tickets.find({})  # TEST
    # await message.answer(f"{data}")   # TEST

    open_count = await db.tickets.count({"status": 'open'})
    in_progress_count = await db.tickets.count({"status": "in_progress"})
    kb = create_inline_kb([[
        (locale.show_new_tickets(), "show_new_tickets"),
        (locale.show_in_progress_tickets(), "show_in_progress_tickets")
    ]])
    await message.answer(locale.status(open_count=open_count, in_progress_count=in_progress_count), reply_markup=kb)

