from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from btc_challenge.users.domain.entity import User


class IUserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> None: ...

    @abstractmethod
    async def get_by_oid(self, oid: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> User | None: ...

    @abstractmethod
    async def get_many(
        self,
        begin_created_at: datetime | None = None,
        end_created_at: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]: ...
