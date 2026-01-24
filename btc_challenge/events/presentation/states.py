from aiogram.fsm.state import State, StatesGroup


class CreateEventStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_start_at = State()
