from aiogram.filters import BaseFilter
from aiogram.types import Message
from fluentogram import TranslatorRunner


class ReplyBtnMenuFilter(BaseFilter):
    async def __call__(self, message: Message, locale: TranslatorRunner) -> bool:
        button_texts = {locale.create_request(), locale.user_requests(), locale.knowledge_base()}
        return message.text in button_texts