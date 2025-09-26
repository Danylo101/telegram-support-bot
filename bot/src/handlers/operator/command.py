from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from bson import ObjectId
from fluentogram import TranslatorRunner

from src.handlers.operator.operator_forms import RespondForm
from src.utils.db import MongoDbClient
from src.utils.keyboards import create_inline_kb
from src.utils.permissions import operator_required

router = Router()


@router.message(Command("status"))
@operator_required
async def status(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    data = await db.tickets.find({})  # TEST
    await message.answer(f"{data}")   # TEST


    open_count = await db.tickets.count({"status": 'open'})
    in_progress_count = await db.tickets.count({"status": "in_progress"})
    kb = create_inline_kb([[
        (locale.show_new_tickets(), "show_new_tickets"),
        (locale.show_in_progress_tickets(), "show_in_progress_tickets")
    ]])
    await message.answer(locale.status(open_count=open_count, in_progress_count=in_progress_count), reply_markup=kb)


@router.message(F.text.startswith("/respond"))
@operator_required
async def respond_by_id(message: Message, locale: TranslatorRunner, state: FSMContext, db: MongoDbClient):
    ticket_id = message.text.replace("/respond", "").strip()
    ticket = await db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if ticket is None:
        await message.answer(locale.ticket_not_found(ticket_id=ticket_id))
    else:
        comments_text = "\n".join(f"💬 {c}" for c in ticket.comments) if ticket.comments else "Немає коментарів"
        await message.answer(locale.ticket(ticket_id="#" + ticket_id, description=ticket.description, status=ticket.status, created_at=ticket.created_at, comments=comments_text))
        await state.set_state(RespondForm.respond)
        await state.update_data(ticket=ticket)
        await message.answer(locale.send_respond())


@router.message(RespondForm.respond)
@operator_required
async def process_respond(message: Message, locale: TranslatorRunner, state: FSMContext):
    await state.update_data(respond=message.text)
    kb = create_inline_kb([[
        (locale.confirm(), "respond_confirm"),
        (locale.cancel(), "respond_cancel")
    ]])
    await message.answer(locale.correct_respond(), reply_markup=kb)
