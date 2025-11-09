from aiogram.fsm.state import StatesGroup, State


class CategoryForm(StatesGroup):
    category_description = State()

class RespondForm(StatesGroup):
    respond = State()

class NoteForm(StatesGroup):
    note = State()

class ArticleForm(StatesGroup):
    title = State()
    content = State()
    category_id = State()


class RequestForm(StatesGroup):
    description = State()

class AddMessageForm(StatesGroup):
    waiting_for_message = State()