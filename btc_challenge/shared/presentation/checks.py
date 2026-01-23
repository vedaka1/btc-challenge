from aiogram.types import Message

from btc_challenge.config import AppConfig
from btc_challenge.users.domain.entity import User


async def require_admin(message: Message, user: User | None) -> bool:
    """Check if user is admin. Returns True if check passed, False otherwise."""
    if not user:
        await message.answer("Сначала нажми /start")
        return False

    if user.telegram_id not in AppConfig.telegram.admin_ids:
        await message.answer("У вас нет доступа к этой команде.")
        return False

    return True


async def require_verified(message: Message, user: User | None) -> bool:
    """Check if user is verified. Returns True if check passed, False otherwise."""
    if not user:
        await message.answer("Сначала нажми /start")
        return False

    if not user.is_verified:
        await message.answer("Ты не верифицирован! Отправь команду /confirmation для верификации.")
        return False

    return True
