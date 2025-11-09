from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from fluentogram import TranslatorRunner

from src.model.models import KnowledgeBaseArticle, Category
from src.utils.db import MongoDbClient
from src.utils.forms import RespondForm, ArticleForm, CategoryForm
from src.utils.keyboards import create_inline_kb
from src.utils.permissions import operator_required

router = Router()


@router.message(Command("status"))
@operator_required
async def status(message: Message, locale: TranslatorRunner, db: MongoDbClient):
    open_count = await db.tickets.count({"status": 'open'})
    in_progress_count = await db.tickets.count({"status": "in_progress"})
    kb = create_inline_kb([[
        (locale.show_new_tickets(), "list_tickets:open:0"),
        (locale.show_in_progress_tickets(), "list_tickets:in_progress:0")
    ]])
    await message.answer(locale.status(open_count=open_count, in_progress_count=in_progress_count), reply_markup=kb)


@router.message(RespondForm.respond)
@operator_required
async def process_respond(message: Message, locale: TranslatorRunner, state: FSMContext):
    await state.update_data(respond=message.text)
    kb = create_inline_kb([[
        (locale.confirm(), "respond_confirm"),
        (locale.cancel(), "respond_cancel")
    ]])
    await message.answer(locale.correct_respond(), reply_markup=kb)


@router.message(Command("add_article"))
@operator_required
async def process_add_article(message: Message, locale: TranslatorRunner, state: FSMContext):
    await message.answer(locale.admin_prompt_article_title())
    await state.set_state(ArticleForm.title)


@router.message(ArticleForm.title)
@operator_required
async def add_title_to_article(message: Message, locale: TranslatorRunner, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(ArticleForm.content)
    await message.answer(locale.admin_prompt_article_content())


@router.message(ArticleForm.content)
@operator_required
async def add_content_to_article(message: Message, locale: TranslatorRunner, state: FSMContext, db: MongoDbClient):
    data = await state.get_data()
    title = data.get("title")
    content = message.text

    operator = await db.users.find_one({"tg_user_id": message.from_user.id})

    ### TODO
    first_category = await db.categories.find_one({})
    if not first_category:
        await message.answer(locale.admin_no_categories_found())
        await state.clear()
        return
    ###

    new_article = KnowledgeBaseArticle(
        title=title,
        content=content,
        category_id=first_category.id,  ## TODO
        author_id=operator.id,
        is_published=True
    )

    await db.knowledge_base.insert_one(new_article.model_dump(by_alias=True))

    await message.answer(locale.admin_article_created(title=title))
    await state.clear()


@router.message(Command("add_category"), F.text)
@operator_required
async def add_category(message: Message, state: FSMContext, locale: TranslatorRunner):
    category_name = message.text.replace("/add_category", "").strip()

    if category_name:
        await message.answer(locale.admin_prompt_category_description())
        await state.update_data(name=category_name)
        await state.set_state(CategoryForm.category_description)
    else:
        await message.answer(locale.admin_prompt_category_name(), parse_mode=None)


@router.message(CategoryForm.category_description)
@operator_required
async def _(message: Message, db: MongoDbClient, state: FSMContext, locale: TranslatorRunner):
    data = await state.get_data()
    name = data.get("name")
    description = message.text

    if not name:
        await message.answer(locale.admin_error_name_not_found())
        await state.clear()
        return

    new_category = Category(name=name, description=description)
    await db.categories.insert_one(new_category.model_dump(by_alias=True))
    await message.answer(locale.admin_category_created(name=name))
    await state.clear()
