from datetime import timezone, datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from bson import ObjectId
from fluentogram import TranslatorRunner

from src.utils.db import MongoDbClient
from src.utils.permissions import operator_required

router = Router()

@router.callback_query(F.data.in_({"show_new_tickets", "show_in_progress_tickets"}))
@operator_required
async def process_status(callback: CallbackQuery, locale: TranslatorRunner, db: MongoDbClient):

    status_filter, status_text = "", ""
    if callback.data == "show_new_tickets":
        status_filter = "open"
        status_text = "Відкриті заявки"
    elif callback.data == "show_in_progress_tickets":
        status_filter = "in_progress"
        status_text = "Заявки в роботі"

    tickets = await db.tickets.find({"status": status_filter})

    if not tickets:
        await callback.message.answer(f"🟢 {status_text} відсутні")
        return

    message_lines = [f"<b>🟢 {status_text}:</b>\n"]
    for ticket in tickets:
        description = ticket.description
        short_desc = (description[:70] + "...") if len(description) > 50 else description
        created_at = ticket.created_at
        if created_at:
            created_str = created_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M")
        else:
            created_str = "—"
        status = ticket.status
        message_lines.append(
            f"• <b>/respond{ticket.id}</b> — {short_desc}\n"
            f"  <i>Статус:</i> {status} 🟢\n"
            f"  <i>Створено:</i> {created_str}\n"
        )

    message_text = "\n".join(message_lines)
    await callback.message.answer(message_text)


@router.callback_query(F.data.in_({"respond_confirm", "respond_cancel"}))
async def process_respond_confirm(callback: CallbackQuery, locale: TranslatorRunner, state: FSMContext, db: MongoDbClient):
    data = await state.get_data()
    respond = data.get("respond")

    if callback.data == "respond_confirm":
        await callback.message.answer(locale.respond_sanded())
        ticket = data.get("ticket")
        await db.tickets.push({"_id": ObjectId(ticket.id)}, "comments", [respond])
        await db.tickets.update_one({"_id": ObjectId(ticket.id)}, {"updated_at": datetime.now(timezone.utc)})
        await state.clear()
    else:
        await callback.message.answer(locale.enter_respond_again())