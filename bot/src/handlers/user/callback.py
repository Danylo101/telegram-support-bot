from datetime import datetime, timezone

import pymongo
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from bson import ObjectId
from fluentogram import TranslatorRunner

from src.utils.forms import RequestForm, AddMessageForm
from src.model.models import Ticket, Message, TicketStatus
from src.utils.db import MongoDbClient

router = Router()


@router.callback_query(F.data.startswith("category:"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext, locale: TranslatorRunner):
    category_id = callback.data.split(":")[-1]

    await state.set_state(RequestForm.description)
    await state.update_data(category_id=category_id)

    await callback.message.answer(locale.describe_problem())


@router.callback_query(F.data.in_({"confirm_description", "cancel_description"}))
async def process_description_confirm(callback: CallbackQuery, state: FSMContext, locale: TranslatorRunner, db: MongoDbClient):
    if callback.data == "cancel_description":
        await callback.message.answer(locale.enter_description_again())
        return

    data = await state.get_data()
    category_id = data.get("category_id")
    description = data.get("description")
    attachment = data.get("attachments", [])

    user = await db.users.find_one({"user_tg_id": callback.from_user.id})

    title = (description[:100] + "...") if len(description) > 100 else description
    seq_id = await get_next_ticket_id(db=db)

    first_message = Message(
        author_id=user.id,
        text=description,
        is_from_support=False,
        attachments=attachment
    )

    ticket = Ticket(
        ticket_seq_id=seq_id,
        title=title,
        user_id=user.id,
        history=[first_message],
        category_id=category_id
    )

    await db.tickets.insert_one(ticket.model_dump(by_alias=True))
    await callback.message.answer(locale.request_saved())
    await state.clear()


async def get_next_ticket_id(db: MongoDbClient) -> int:
    cursor = db.tickets.collection.find(
        filter={},
        projection={"ticket_seq_id": 1},
        sort=[("ticket_seq_id", pymongo.DESCENDING)],
        limit=1
    )
    last_tickets_list = await cursor.to_list(length=1)

    if last_tickets_list:
        last_ticket = last_tickets_list[0]
        last_id = last_ticket.get("ticket_seq_id", 0)
        return last_id + 1

    return 1


@router.callback_query(F.data.startswith("add_message:"))
async def process_add_message_start(callback: CallbackQuery, state: FSMContext, locale: TranslatorRunner, db: MongoDbClient):
    try:
        ticket_id_str = callback.data.split(":")[-1]
        ticket_id = ObjectId(ticket_id_str)
    except Exception:
        await callback.answer(locale.invalid_ticket_id(), show_alert=True)
        return

    user = await db.users.find_one({"user_tg_id": callback.from_user.id})
    ticket = await db.tickets.find_one({"_id": ticket_id})

    if not user or not ticket or ticket.user_id != user.id:
        await callback.answer(locale.ticket_not_found_or_no_access(), show_alert=True)
        return

    if ticket.status == TicketStatus.CLOSED:
        await callback.answer(locale.cannot_add_message_ticket_closed(), show_alert=True)
        return

    await state.set_state(AddMessageForm.waiting_for_message)
    await state.update_data(ticket_id=ticket_id_str)

    await callback.message.answer(locale.prompt_add_clarification())
    await callback.answer()


@router.callback_query(F.data.startswith("close_ticket:"))
async def process_close_ticket(callback: CallbackQuery, locale: TranslatorRunner, db: MongoDbClient):
    try:
        ticket_id_str = callback.data.split(":")[-1]
        ticket_id = ObjectId(ticket_id_str)
    except Exception:
        await callback.answer(locale.error_ticket_id(), show_alert=True)
        return

    user = await db.users.find_one({"user_tg_id": callback.from_user.id})
    ticket = await db.tickets.find_one({"_id": ticket_id})

    if not user or not ticket or ticket.user_id != user.id:
        await callback.answer(locale.ticket_not_found_or_no_access(), show_alert=True)
        return

    if ticket.status == TicketStatus.CLOSED:
        await callback.answer(locale.ticket_already_closed(), show_alert=True)
        return

    await db.tickets.update_one(
        {"_id": ticket.id},
        {
            "status": TicketStatus.CLOSED.value,
            "closed_at": datetime.now(timezone.utc),
            "resolved_at": datetime.now(timezone.utc)
        }
    )

    await callback.message.answer(locale.ticket_closed_success(ticket_seq_id=ticket.ticket_seq_id))
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()


@router.callback_query(F.data.startswith("show_article:"))
async def process_show_article(callback: CallbackQuery, locale: TranslatorRunner, db: MongoDbClient):
    try:
        article_id_str = callback.data.split(":")[-1]
        article_id = ObjectId(article_id_str)
    except Exception:
        await callback.answer(locale.error_data(), show_alert=True)
        return

    article = await db.knowledge_base.find_one({"_id": article_id})

    if not article or not article.is_published:
        await callback.answer(locale.article_not_found(), show_alert=True)
        return

    text = f"<b>{article.title}</b>\n\n{article.content}"

    await callback.message.answer(text)
    await callback.answer()
