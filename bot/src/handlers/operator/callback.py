from aiogram import Router, F
from aiogram.types import CallbackQuery
from fluentogram import TranslatorRunner

from src.utils.db import MongoDbClient
from src.utils.keyboards import create_inline_kb

router = Router()

@router.callback_query(F.data.in_({"show_new_tickets", "show_in_progress_tickets"}))
async def process_status(callback: CallbackQuery, locale: TranslatorRunner, db: MongoDbClient):
    status_filter = None
    if callback.data == "show_new_tickets":
        status_filter = "open"
    elif callback.data == "show_in_progress_tickets":
        status_filter = "in_progress"

    tickets = await db.tickets.find({"status": status_filter})
    buttons = [
        [(f"#{ticket.id} - {ticket.description[:20]}", f"ticket:{ticket.id}")]
        for ticket in tickets
    ]

    kb = create_inline_kb(buttons)

    await callback.message.answer("Відкриті1 заявки", reply_markup=kb)