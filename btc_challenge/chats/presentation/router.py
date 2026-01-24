import logging

from aiogram import Router, types
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from punq import Container

from btc_challenge.chats.application.interactors.create import CreateChatInteractor
from btc_challenge.chats.application.interactors.deactivate import DeactivateChatInteractor

chats_router = Router()
logger = logging.getLogger(__name__)


@chats_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_chat(event: types.ChatMemberUpdated, container: Container) -> None:
    """Handle bot being added to a group."""
    chat = event.chat

    if chat.type not in ["group", "supergroup"]:
        return

    logger.info(f"Bot added to chat: {chat.id} ({chat.title})")

    interactor: CreateChatInteractor = container.resolve(CreateChatInteractor)
    await interactor.execute(
        telegram_chat_id=chat.id,
        chat_type=chat.type,
        title=chat.title,
    )

    logger.info(f"Chat {chat.id} saved to database")


@chats_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER))
async def bot_removed_from_chat(event: types.ChatMemberUpdated, container: Container) -> None:
    """Handle bot being removed from a group."""
    chat = event.chat

    if chat.type not in ["group", "supergroup"]:
        return

    logger.info(f"Bot removed from chat: {chat.id} ({chat.title})")

    interactor: DeactivateChatInteractor = container.resolve(DeactivateChatInteractor)
    await interactor.execute(telegram_chat_id=chat.id)

    logger.info(f"Chat {chat.id} deactivated in database")
