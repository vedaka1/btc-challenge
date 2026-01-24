from btc_challenge.chats.domain.entity import Chat
from btc_challenge.chats.domain.repository import IChatRepository


class GetAllChatsInteractor:
    def __init__(self, chat_repository: IChatRepository):
        self._chat_repository = chat_repository

    async def execute(self, is_active: bool | None = None) -> list[Chat]:
        return await self._chat_repository.get_many(is_active=is_active)
