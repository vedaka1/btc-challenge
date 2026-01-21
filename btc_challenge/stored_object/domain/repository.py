from abc import ABC, abstractmethod
from uuid import UUID

from btc_challenge.stored_object.domain.entity import StoredObject


class IStoredObjectRepository(ABC):
    @abstractmethod
    async def create(self, stored_object: StoredObject) -> None: ...

    @abstractmethod
    async def get_by_oid(self, oid: UUID) -> StoredObject | None: ...

    @abstractmethod
    async def delete(self, oid: UUID) -> None: ...

    @abstractmethod
    async def get_many(self, limit: int = 100, offset: int = 0) -> list[StoredObject]: ...
