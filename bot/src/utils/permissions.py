from functools import wraps

from aiogram.dispatcher.event.bases import (SkipHandler)

from src.utils.config import settings

def is_operator(user_id):
    return user_id in settings.OPERATOR_IDS

def is_admin(user_id):
    return settings.ADMIN_ID == user_id


def operator_required(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        user = getattr(event, "from_user", None)
        if user is None:
            return SkipHandler()

        user_id = user.id
        if not (is_operator(user_id) or is_admin(user_id)):
            return SkipHandler()

        return await handler(event, *args, **kwargs)
    return wrapper


def admin_required(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        user = getattr(event, "from_user", None)
        if user is None:
            raise SkipHandler()

        if not is_admin(user.id):
            raise SkipHandler()

        return await handler(event,  *args, **kwargs)
    return wrapper