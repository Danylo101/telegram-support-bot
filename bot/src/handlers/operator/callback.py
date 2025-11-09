from datetime import timezone, datetime
from typing import List

from aiogram import Router, F
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp.web_urldispatcher import html_escape
from fluentogram import TranslatorRunner
from src.model.models import Ticket, Message, TicketStatus, InternalNote
from src.utils.db import MongoDbClient
from src.utils.permissions import operator_required
from src.utils.forms import RespondForm, NoteForm
from src.utils.keyboards import create_inline_kb

router = Router()

TICKETS_PER_PAGE = 5


@router.callback_query(F.data.startswith("list_tickets:"))
@operator_required
async def process_ticket_list(callback: CallbackQuery, locale: TranslatorRunner, db: MongoDbClient):
    try:
        _, status_str, page_str = callback.data.split(":")
        page = int(page_str)
        status_filter = TicketStatus(status_str)
    except ValueError:
        await callback.answer(locale.error_data(), show_alert=True)
        return

    offset = page * TICKETS_PER_PAGE

    tickets: List[Ticket] = await db.tickets.find(
        {"status": status_filter.value},
        count=TICKETS_PER_PAGE,
        offset=offset,
    )

    total_tickets = await db.tickets.count({"status": status_filter.value})
    total_pages = (total_tickets + TICKETS_PER_PAGE - 1) // TICKETS_PER_PAGE
    if total_pages == 0:
        total_pages = 1

    status_text = locale.status_text_open() if status_filter == TicketStatus.OPEN else locale.status_text_in_progress()

    if not tickets:
        await callback.message.edit_text(
            locale.operator_tickets_empty(status_text=status_text)
        )
        return

    keyboard_buttons = []
    for ticket in tickets:
        short_desc = (ticket.title[:30] + "...") if len(ticket.title) > 30 else ticket.title
        button_text = locale.operator_ticket_list_item(ticket_seq_id=ticket.ticket_seq_id, short_desc=short_desc)
        button_callback = f"view_ticket:{ticket.ticket_seq_id}"
        keyboard_buttons.append(
            [InlineKeyboardButton(text=button_text, callback_data=button_callback)]
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text=locale.pagination_back(), callback_data=f"list_tickets:{status_str}:{page - 1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(text=locale.pagination_next(), callback_data=f"list_tickets:{status_str}:{page + 1}")
        )

    if nav_buttons:
        keyboard_buttons.append(nav_buttons)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    text = locale.operator_ticket_list_header(
        status_text=status_text,
        page=page + 1,
        total_pages=total_pages
    )

    await callback.message.edit_text(text, reply_markup=markup)


@router.callback_query(F.data.startswith("view_ticket:"))
@operator_required
async def process_view_ticket(callback: CallbackQuery, locale: TranslatorRunner, db: MongoDbClient):
    ticket_seq_id_str = callback.data.split(":")[-1]

    try:
        ticket_seq_id = int(ticket_seq_id_str)
    except ValueError:
        await callback.answer(locale.invalid_ticket_id(), show_alert=True)
        return

    ticket: Ticket = await db.tickets.find_one({"ticket_seq_id": ticket_seq_id})

    if ticket is None:
        await callback.message.answer(locale.ticket_not_found(ticket_id=ticket_seq_id_str))
        await callback.answer()
        return

    client_user = await db.users.find_one({"_id": ticket.user_id})
    client_str = f"{client_user.first_name} {client_user.last_name or ''}" if client_user else locale.unknown_user_fallback()
    client_phone = client_user.phone if client_user and client_user.phone else locale.not_specified()

    category_str = locale.no_category()
    if ticket.category_id:
        category = await db.categories.find_one({"_id": ticket.category_id})
        category_str = category.name if category else locale.unknown_category()

    created_str = ticket.created_at.strftime('%d.%m.%Y %H:%M')
    updated_str = ticket.updated_at.strftime('%d.%m.%Y %H:%M')
    sla_str = ticket.sla_due_at.strftime('%d.%m.%Y %H:%M') if ticket.sla_due_at else locale.not_set()

    has_attachments = False
    attachments_count = 0
    history_lines = []

    if not ticket.history:
        history_str = locale.no_messages()
    else:
        for msg in ticket.history:
            msg_attachment_text = ""
            if msg.attachments:
                has_attachments = True
                count = len(msg.attachments)
                attachments_count += count
                msg_attachment_text = locale.attachment_count(count=count)

            author = locale.support_author() if msg.is_from_support else locale.client_author()
            time = msg.timestamp.strftime('%d.%m %H:%M')
            history_lines.append(f"<b>{author}</b> ({time}): {html_escape(msg.text)}{msg_attachment_text}")
        history_str = "\n\n".join(history_lines)

    if not ticket.internal_notes:
        notes_str = locale.no_notes()
    else:
        notes_lines = []
        for note in ticket.internal_notes:
            author = await db.users.find_one({"_id": note.author_id})
            author_name = f"{author.first_name}" if author else locale.system_author()
            time = note.timestamp.strftime('%d.%m %H:%M')
            notes_lines.append(f"<b>{author_name}</b> ({time}): {html_escape(note.text)}")
        notes_str = "\n".join(notes_lines)

    kb_buttons = [[
        InlineKeyboardButton(text=locale.add_note(), callback_data=f"add_note_to:{ticket.ticket_seq_id}")
    ]]
    if has_attachments:
        kb_buttons[0].append(
            InlineKeyboardButton(
                text=locale.view_attachments(count=attachments_count),
                callback_data=f"view_attachments:{ticket.ticket_seq_id}"
            )
        )

    kb_buttons.append([InlineKeyboardButton(text=locale.reply(), callback_data=f"respond_to:{ticket.ticket_seq_id}")])
    markup = InlineKeyboardMarkup(inline_keyboard=kb_buttons)

    tags = html_escape(', '.join(ticket.tags)) if ticket.tags else locale.tags_none()
    text = locale.operator_ticket_view(
        ticket_seq_id=ticket.ticket_seq_id,
        client_str=html_escape(client_str),
        client_phone=html_escape(client_phone),
        category_str=html_escape(category_str),
        status=ticket.status.value,
        priority=ticket.priority.value,
        tags=tags,
        created_str=created_str,
        updated_str=updated_str,
        sla_str=sla_str,
        history=history_str,
        notes=notes_str
    )

    await callback.message.answer(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("view_attachments:"))
@operator_required
async def process_view_attachments(callback: CallbackQuery, locale: TranslatorRunner, db: MongoDbClient):
    ticket_seq_id_str = callback.data.split(":")[-1]
    try:
        ticket_seq_id = int(ticket_seq_id_str)
    except ValueError:
        await callback.answer(locale.error_ticket_id(), show_alert=True)
        return

    ticket: Ticket = await db.tickets.find_one({"ticket_seq_id": ticket_seq_id})
    if not ticket:
        await callback.answer(locale.ticket_not_found(ticket_id=ticket_seq_id_str), show_alert=True)
        return

    all_attachments = []
    for msg in ticket.history:
        if msg.attachments:
            all_attachments.extend(msg.attachments)

    if not all_attachments:
        await callback.message.answer(locale.no_attachments_in_ticket())
        await callback.answer()
        return

    await callback.message.answer(locale.attachments_for_ticket(ticket_seq_id=ticket.ticket_seq_id))
    for att in all_attachments:
        try:
            if att.mime_type.startswith("image/"):
                await callback.message.answer_photo(att.file_id)
            else:
                await callback.message.answer_document(att.file_id)
        except Exception as e:
            await callback.message.answer(locale.error_loading_attachment(file_unique_id=att.file_unique_id))

    await callback.answer()


@router.callback_query(F.data.startswith("respond_to:"))
@operator_required
async def process_start_respond(callback: CallbackQuery, locale: TranslatorRunner, state: FSMContext,
                                db: MongoDbClient):
    ticket_seq_id_str = callback.data.split(":")[-1]
    try:
        ticket_seq_id = int(ticket_seq_id_str)
    except ValueError:
        await callback.answer(locale.error_ticket_id(), show_alert=True)
        return

    ticket: Ticket = await db.tickets.find_one({"ticket_seq_id": ticket_seq_id})
    if ticket is None:
        await callback.answer(locale.ticket_not_found(ticket_id=ticket_seq_id_str), show_alert=True)
        return

    await state.set_state(RespondForm.respond)
    await state.update_data(ticket=ticket)
    await callback.message.answer(locale.send_respond())
    await callback.answer()


@router.callback_query(F.data.in_({"respond_confirm", "respond_cancel"}))
@operator_required
async def process_respond_confirm(callback: CallbackQuery, locale: TranslatorRunner, state: FSMContext,
                                  db: MongoDbClient):
    if callback.data == "respond_cancel":
        await callback.message.edit_text(locale.enter_respond_again())
        await state.set_state(RespondForm.respond)
        return

    data = await state.get_data()
    respond_text = data.get("respond")

    ticket: Ticket = data.get("ticket")
    if not ticket or not respond_text:
        await callback.message.answer(locale.state_error_data_lost())
        await state.clear()
        return

    operator = await db.users.find_one({"user_tg_id": callback.from_user.id})
    if not operator:
        await callback.message.answer(locale.unknown_user())
        return

    new_message = Message(
        author_id=operator.id,
        text=respond_text,
        is_from_support=True
    )

    await db.tickets.update_one(
        {"_id": ticket.id},
        {
            "status": TicketStatus.IN_PROGRESS.value,
            "updated_at": datetime.now(timezone.utc)
        }
    )

    await db.tickets.push(
        {"_id": ticket.id},
        "history",
        new_message.model_dump()
    )

    client = await db.users.find_one({"_id": ticket.user_id})
    try:
        if client and client.user_tg_id:
            message_text = locale.user_new_reply_notification(
                ticket_seq_id=ticket.ticket_seq_id,
                text=html_escape(respond_text)
            )
            await callback.bot.send_message(
                chat_id=client.user_tg_id,
                text=message_text,
                reply_markup=create_inline_kb([
                    [
                        (locale.clarify_problem(), f"add_message:{ticket.id}"),
                        (locale.close_ticket(), f"close_ticket:{ticket.id}")
                    ]
                ])
            )
        else:
            await callback.message.answer(locale.user_not_found())
    except TelegramAPIError as e:
        print(f"Error while send message to user with ID {client.user_tg_id}: {e}")
        await callback.message.answer(locale.operator_reply_saved_not_sent())

    await callback.message.edit_text(locale.respond_sanded())
    await state.clear()


@router.callback_query(F.data.startswith("add_note_to:"))
@operator_required
async def process_start_add_note(callback: CallbackQuery, locale: TranslatorRunner, state: FSMContext,
                                 db: MongoDbClient):
    ticket_seq_id_str = callback.data.split(":")[-1]
    try:
        ticket_seq_id = int(ticket_seq_id_str)
    except ValueError:
        await callback.answer(locale.error_ticket_id(), show_alert=True)
        return

    ticket: Ticket = await db.tickets.find_one({"ticket_seq_id": ticket_seq_id})
    if ticket is None:
        await callback.answer(locale.ticket_not_found(ticket_id=ticket_seq_id_str), show_alert=True)
        return

    await state.set_state(NoteForm.note)
    await state.update_data(ticket=ticket)

    await callback.message.answer(locale.operator_prompt_internal_note())
    await callback.answer()


@router.message(NoteForm.note)
@operator_required
async def process_submit_note(message: Message, locale: TranslatorRunner, state: FSMContext):
    await state.update_data(note_text=message.text)

    kb = create_inline_kb([[
        (locale.confirm(), "note_confirm"),
        (locale.cancel(), "note_cancel")
    ]])
    await message.answer(locale.operator_confirm_note(text=html_escape(message.text)), reply_markup=kb)


@router.callback_query(F.data.in_({"note_confirm", "note_cancel"}))
@operator_required
async def process_submit_note_confirm(callback: CallbackQuery, locale: TranslatorRunner, state: FSMContext,
                                      db: MongoDbClient):
    data = await state.get_data()

    if callback.data == "note_confirm":
        ticket: Ticket = data.get("ticket")
        note_text = data.get("note_text")

        if not ticket or not note_text:
            await callback.message.answer(locale.state_error_data_lost())
            await state.clear()
            return

        operator = await db.users.find_one({"user_tg_id": callback.from_user.id})
        if not operator:
            await callback.message.answer(locale.unknown_user())
            return

        new_note = InternalNote(
            author_id=operator.id,
            text=note_text
        )

        await db.tickets.push(
            {"_id": ticket.id},
            "internal_notes",
            new_note.model_dump()
        )

        await db.tickets.update_one(
            {"_id": ticket.id},
            {"updated_at": datetime.now(timezone.utc)}
        )

        await callback.message.edit_text(locale.operator_note_added())
    else:
        await callback.message.edit_text(locale.operator_note_cancelled())

    await state.clear()
    await callback.answer()
