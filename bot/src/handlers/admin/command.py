from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from fluentogram import TranslatorRunner
from src.utils.db import MongoDbClient
from src.utils.permissions import admin_required

router = Router()


@router.message(Command("clear"))
@admin_required
async def _(message: Message, db: MongoDbClient, locale: TranslatorRunner): ## TEST ##
    await db.tickets.delete_many({})
    await db.users.delete_many({})
    await message.answer(locale.admin_db_cleared())

