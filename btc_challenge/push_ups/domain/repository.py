from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from btc_challenge.push_ups.domain.entity import PushUp


class IPushUpRepository(ABC):
    @abstractmethod
    async def create(self, push_up: PushUp) -> None: ...

    @abstractmethod
    async def get_by_oid(self, push_up_id: UUID) -> PushUp | None: ...

    @abstractmethod
    async def get_by_user_oid(self, user_oid: UUID, limit: int = 100, offset: int = 0) -> list[PushUp]: ...

    @abstractmethod
    async def get_by_user_oid_and_date(
        self,
        user_oid: UUID,
        begin_date: datetime,
        end_date: datetime,
    ) -> list[PushUp]: ...
