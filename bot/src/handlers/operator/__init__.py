__all__ = ("router", )

from aiogram import Router
from .command import router as command_router
from .callback import router as callback_router

router = Router()
router.include_routers(callback_router, command_router)