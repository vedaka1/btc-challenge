from abc import ABC, abstractmethod
from uuid import UUID

from btc_challenge.chats.domain.entity import Chat


class IChatRepository(ABC):
    @abstractmethod
    async def create(self, chat: Chat) -> None:
        pass

    @abstractmethod
    async def update(self, chat: Chat) -> None:
        pass

    @abstractmethod
    async def get_by_oid(self, oid: UUID) -> Chat | None:
        pass

    @abstractmethod
    async def get_by_telegram_chat_id(self, telegram_chat_id: int) -> Chat | None:
        pass

    @abstractmethod
    async def get_many(self, is_active: bool | None = None) -> list[Chat]:
        pass
