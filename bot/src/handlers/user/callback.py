from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from fluentogram import TranslatorRunner

from src.handlers.user.user_forms import RegisterForm, RequestForm
from src.model.ticket import Ticket
from src.utils.db import MongoDbClient


router = Router()


@router.callback_query(F.data == "create_request")
async def create_request(callback: CallbackQuery, locale: TranslatorRunner, db: MongoDbClient, state: FSMContext):
    user = await db.user.find_one({"id": callback.from_user.id})

    if not user:
        await callback.message.answer(locale.unknown_user())
        await state.set_state(RegisterForm.name)
        return

    await callback.message.answer(locale.describe_problem())
    await state.set_state(RequestForm.description)

@router.callback_query(F.data.in_({"confirm_name", "cancel_name"}))
async def process_name_confirm(callback: CallbackQuery, state: FSMContext, locale: TranslatorRunner, db: MongoDbClient):
    data = await state.get_data()
    name = data.get("name")

    if callback.data == "confirm_name":
        await db.user.insert_one({"id": callback.from_user.id, "name": name})
        await callback.message.answer(locale.name_saved())
        await state.clear()
    else:
        await callback.message.answer(locale.enter_name_again())


@router.callback_query(F.data.in_({"confirm_description", "cancel_description"}))
async def process_description_confirm(callback: CallbackQuery, state: FSMContext, locale: TranslatorRunner, db: MongoDbClient):
    data = await state.get_data()
    description = data.get("description")

    if callback.data == "confirm_description":
        ticket = Ticket(user_id=callback.from_user.id, description=description)
        await db.tickets.insert_one(ticket.model_dump())
        await callback.message.answer(locale.request_saved())
        await state.clear()
    else:
        await callback.message.answer(locale.enter_description_again())