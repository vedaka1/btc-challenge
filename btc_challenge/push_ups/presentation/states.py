from aiogram.fsm.state import State, StatesGroup


class PushUpStates(StatesGroup):
    waiting_for_count = State()
    waiting_for_video = State()
