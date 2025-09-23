from aiogram.fsm.state import StatesGroup, State


class RegisterForm(StatesGroup):
    name = State()

class RequestForm(StatesGroup):
    description = State()