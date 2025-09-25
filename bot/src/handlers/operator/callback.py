from datetime import timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery
from fluentogram import TranslatorRunner

from src.utils.db import MongoDbClient

router = Router()

@router.callback_query(F.data.in_({"show_new_tickets", "show_in_progress_tickets"}))
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
            f"• <b>#{ticket.id}</b> — {short_desc}\n"
            f"  <i>Статус:</i> {status} 🟢\n"
            f"  <i>Створено:</i> {created_str}\n"
        )

    message_text = "\n".join(message_lines)
    await callback.message.answer(message_text)
