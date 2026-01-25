from btc_challenge.chats.domain.entity import Chat
from btc_challenge.chats.domain.repository import IChatRepository
from btc_challenge.shared.application.commiter import ICommiter


class CreateChatInteractor:
    def __init__(self, chat_repository: IChatRepository, commiter: ICommiter):
        self._chat_repository = chat_repository
        self._commiter = commiter

    async def execute(
        self,
        telegram_chat_id: int,
        chat_type: str,
        title: str | None = None,
    ) -> Chat:
        # Validate chat_type
        if chat_type not in ("group", "supergroup"):
            msg = f"Invalid chat_type: {chat_type}. Must be 'group' or 'supergroup'"
            raise ValueError(msg)

        # Check if chat already exists
        existing_chat = await self._chat_repository.get_by_telegram_chat_id(telegram_chat_id)
        if existing_chat:
            # Reactivate if it was deactivated
            if not existing_chat.is_active:
                existing_chat.is_active = True
                await self._chat_repository.update(existing_chat)
                await self._commiter.commit()
            return existing_chat

        chat = Chat.create(
            telegram_chat_id=telegram_chat_id,
            chat_type=chat_type,
            title=title,
        )
        await self._chat_repository.create(chat)
        await self._commiter.commit()
        return chat
