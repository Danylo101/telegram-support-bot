import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from fluentogram import TranslatorHub
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class TranslateMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        language = data['user'].language_code if 'user' in data else 'uk'
        hub: TranslatorHub = data.get('t_hub')
        data['locale'] = hub.get_translator_by_locale(language)

        return await handler(event, data)


class DataBaseMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    """
    Data base middleware
    """

    def __init__(self, db: AsyncIOMotorClient):
        super().__init__()
        self.db = db

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        data["db"] = self.db
        return await handler(event, data)
