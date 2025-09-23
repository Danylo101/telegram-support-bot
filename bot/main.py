import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from fluent_compiler.bundle import FluentBundle
from fluentogram import TranslatorHub, FluentTranslator

from src.utils.db import db
from src.utils.config import settings
from src.handlers import router as main_router
from src.utils.middelware import TranslateMiddleware, DataBaseMiddleware

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

t_hub = TranslatorHub(
    {
        "uk": ("uk",)
    },
    translators=[
        FluentTranslator(
            "uk",
            translator=FluentBundle.from_files(
                "uk-UA",

                filenames=[
                    "src/i18n/uk/text.ftl",
                    "src/i18n/uk/button.ftl",
                ]
            ),
        )
    ],
    root_locale="uk",
)

async def main():
    session = AiohttpSession()
    bot = Bot(
        token=settings.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher(t_hub=t_hub)

    dp.message.outer_middleware(TranslateMiddleware())
    dp.message.outer_middleware(DataBaseMiddleware(db=db))

    dp.callback_query.outer_middleware(TranslateMiddleware())
    dp.callback_query.outer_middleware(DataBaseMiddleware(db=db))

    dp.include_router(main_router)

    try:
        await dp.start_polling(bot)
    except ValueError as e:
        log.error("ValueError occurred: %s: ", e)
    except KeyError as e:
        log.error("KeyError occurred: %s:", e)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())