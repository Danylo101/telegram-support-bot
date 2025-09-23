__all__ = ("router", )

from aiogram import Router
from .user import router as user_router
from .operator import router as operator_router
from .admin import router as admin_router

router = Router()
router.include_routers(user_router, operator_router, admin_router)