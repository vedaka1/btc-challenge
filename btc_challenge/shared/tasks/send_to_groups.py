import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from btc_challenge.chats.adapters.sqlite.repository import ChatRepository

logger = logging.getLogger(__name__)


async def send_notification_to_groups(
    bot: Bot,
    session: AsyncSession,
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
) -> None:
    """Send notification to all active groups.

    Args:
        bot: Telegram bot instance
        session: Database session
        text: Message text to send
        keyboard: Optional inline keyboard
    """
    chat_repository = ChatRepository(session)
    chats = await chat_repository.get_many(is_active=True)

    for chat in chats:
        try:
            await bot.send_message(
                chat_id=chat.telegram_chat_id,
                text=text,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.warning("Failed to send notification to chat %s: %s", chat.telegram_chat_id, e)
            chat.deactivate()
            await chat_repository.update(chat)
