import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import TelegramObject, Update
from fluentogram import TranslatorHub
from cachetools import TTLCache
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

caches = {
    "default": TTLCache(maxsize=10_000, ttl=0.1)
}

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


class ThrottlingMiddleware(BaseMiddleware):  # pylint: disable=too-few-public-methods
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        if not hasattr(event, "from_user") or event.from_user is None:
            return await handler(event, data)

        if event.from_user.id in caches["default"]:
            return SkipHandler()
        caches["default"][event.from_user.id] = None
        return await handler(event, data)

