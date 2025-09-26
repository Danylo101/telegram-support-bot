from aiogram.fsm.state import StatesGroup, State


class RespondForm(StatesGroup):
    respond = State()