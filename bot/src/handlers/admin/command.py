

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.utils.db import MongoDbClient
from src.utils.permissions import admin_required

router = Router()


@router.message(Command("clear"))
@admin_required
async def _(message: Message, db: MongoDbClient):
    await db.tickets.delete_many({})
    await db.user.delete_many({})
    await message.answer("clear (:")

