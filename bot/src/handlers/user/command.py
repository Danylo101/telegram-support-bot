from datetime import timezone, datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Contact, ReplyKeyboardMarkup, KeyboardButton
from aiohttp.web_urldispatcher import html_escape
from bson import ObjectId
from fluentogram import TranslatorRunner

from src.model import models
from src.model.models import User, Attachment, TicketStatus
from src.utils.db import MongoDbClient
from src.utils.forms import RequestForm, AddMessageForm
from src.utils.filter import ReplyBtnMenuFilter
from src.utils.keyboards import create_inline_kb, create_reply_kb
from src.utils.permissions import is_operator, is_admin

router = Router()


@router.message(Command("start"))
async def start(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    user = await db.users.find_one({"user_tg_id": message.from_user.id})
    if user is None:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=locale.share_contact(), request_contact=True)]], resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(locale.prompt_share_contact(), reply_markup=kb)
    else:
        kb = create_reply_kb([
            [(locale.create_request()),
             (locale.user_requests())
             ],
            [(locale.knowledge_base())]
        ])
        await message.answer(locale.start(first_name=message.from_user.first_name), reply_markup=kb)


@router.message(lambda msg: msg.contact is not None)
async def get_contact(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    contact: Contact = message.contact
    user_info = message.from_user
    user = User(
        user_tg_id=user_info.id,
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        username=user_info.username,
        phone=contact.phone_number
    )
    await db.users.insert_one(user.model_dump(by_alias=True))
    await message.answer(locale.contact_saved(phone_number=contact.phone_number))
    kb = create_reply_kb([[
        (locale.create_request()),
        (locale.user_requests())
    ]])
    await message.answer(locale.start(first_name=message.from_user.first_name), reply_markup=kb)


@router.message(RequestForm.description)
async def process_description(message: Message, locale: TranslatorRunner, state: FSMContext, db: MongoDbClient):
    attachments = []
    if message.photo:
        user = await db.users.find_one({"user_tg_id": message.from_user.id})
        if not user:
            await message.answer(locale.unknown_user())
            return

        photo = message.photo[-1]

        new_attachment = Attachment(
            file_unique_id=photo.file_unique_id,
            file_id=photo.file_id,
            mime_type="image/jpeg",
            uploaded_by=user.id
        )
        attachments.append(new_attachment)

        if message.caption:
            description = message.caption.strip()
        else:
            await message.answer(locale.add_description_to_photo())
            return


    elif message.text:
        description = message.text.strip()

    else:
        await message.answer(locale.send_description_text_or_photo())
        return

    kb = create_inline_kb([[
        (locale.confirm(), "confirm_description"),
        (locale.cancel(), "cancel_description")
    ]])
    await state.update_data(description=description, attachments=attachments)
    await message.answer(locale.is_correct_description(), reply_markup=kb)


@router.message(ReplyBtnMenuFilter())
async def handle_reply_btn(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    user = await db.users.find_one({"user_tg_id": message.from_user.id})
    if not user:
        await message.answer(locale.unknown_user())
        return
    else:
        text = message.text
        if text == locale.create_request():
            categories = await db.categories.find({})
            kb = create_inline_kb([
                [(category.name, f"category:{str(category.id)}")]
                for category in categories
            ])
            await message.answer(locale.select_category(), reply_markup=kb)
        elif text == locale.user_requests():
            tickets = await db.tickets.find({"user_id": user.id})
            if not tickets:
                await message.answer(locale.tickets_empty())
                return

            message_lines = []
            for ticket in tickets:
                created_str = (
                    ticket.created_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M")
                    if ticket.created_at
                    else "—"
                )

                message_lines.append(
                    locale.ticket_short_item(
                        id="#" + str(ticket.ticket_seq_id),
                        short_desc=ticket.title,
                        status=ticket.status.value,
                        created_at=created_str,
                    )
                )
                message_lines.append("")

            message_lines.append(locale.ticket_footer())
            await message.answer("\n".join(message_lines))
        elif text == locale.knowledge_base():
            articles = await db.knowledge_base.find({"is_published": True})
            if not articles:
                await message.answer(locale.articles_empty())
                return

            kb = create_inline_kb([
                [(article.title, f"show_article:{str(article.id)}")]
                for article in articles
            ])
            await message.answer(locale.select_article(), reply_markup=kb)


@router.message(F.text.startswith("#"))
async def send_ticket_info(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    try:
        ticket_seq_id = int(message.text.replace("#", "").strip())
        ticket = await db.tickets.find_one({"ticket_seq_id": ticket_seq_id})
    except ValueError:
        await message.answer(locale.invalid_ticket_id())
        return

    if not ticket:
        await message.answer(locale.ticket_not_found(ticket_id=ticket_seq_id))
        return

    user = await db.users.find_one({"_id": ticket.user_id})
    if not user:
        await message.answer(locale.unknown_user())
        return

    if user.user_tg_id != message.from_user.id:
        if not (is_operator(message.from_user.id) or is_admin(message.from_user.id)):
            return

    attachments_count = 0
    history_lines = []
    if not ticket.history:
        history_str = locale.no_messages()
    else:
        for msg in ticket.history:
            msg_attachment_text = ""
            if msg.attachments:
                count = len(msg.attachments)
                attachments_count += count
                msg_attachment_text = locale.attachment_count(count=count)

            author = locale.support_author() if msg.is_from_support else locale.client_author()
            time = msg.timestamp.strftime('%d.%m %H:%M')
            history_lines.append(f"<b>{author}</b> ({time}): {html_escape(msg.text)}{msg_attachment_text}")
        history_str = "\n\n".join(history_lines)

    await message.answer(locale.ticket(
        ticket_id=f"#{ticket_seq_id}",
        description=ticket.title,
        comments=history_str,
        status=ticket.status,
        created_at=ticket.created_at
    ))


@router.message(AddMessageForm.waiting_for_message)
async def process_add_message_receive(message: Message, locale: TranslatorRunner, state: FSMContext, db: MongoDbClient):
    data = await state.get_data()
    ticket_id_str = data.get("ticket_id")
    if not ticket_id_str:
        await message.answer(locale.state_error_data_lost())
        await state.clear()
        return

    user = await db.users.find_one({"user_tg_id": message.from_user.id})
    if not user:
        await message.answer(locale.unknown_user())
        await state.clear()
        return

    attachments = []

    if message.photo:
        photo = message.photo[-1]
        new_attachment = Attachment(
            file_unique_id=photo.file_unique_id,
            file_id=photo.file_id,
            mime_type="image/jpeg",
            uploaded_by=user.id
        )
        attachments.append(new_attachment)
        if message.caption:
            description = message.caption.strip()
        else:
            await message.answer(locale.add_description_to_photo())
            return

    elif message.text:
        description = message.text.strip()
    else:
        await message.answer(locale.send_description_text_or_photo())
        return

    new_message = models.Message(
        author_id=user.id,
        text=description,
        is_from_support=False,
        attachments=attachments
    )

    ticket_id = ObjectId(ticket_id_str)

    await db.tickets.push(
        {"_id": ticket_id},
        "history",
        new_message.model_dump(by_alias=True)
    )

    await db.tickets.update_one(
        {"_id": ticket_id},
        {
            "status": TicketStatus.OPEN.value,
            "updated_at": datetime.now(timezone.utc)
        }
    )

    await message.answer(locale.message_added_to_ticket())
    await state.clear()
