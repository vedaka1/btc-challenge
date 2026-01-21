from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_challenge.stored_object.adapters.sqlite.mapper import SqliteStoredObjectMapper
from btc_challenge.stored_object.adapters.sqlite.model import StoredObjectORM
from btc_challenge.stored_object.domain.entity import StoredObject
from btc_challenge.stored_object.domain.repository import IStoredObjectRepository


class StoredObjectRepository(IStoredObjectRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = SqliteStoredObjectMapper

    async def create(self, stored_object: StoredObject) -> None:
        orm = self._mapper.to_model(stored_object)
        self._session.add(orm)

    async def get_by_oid(self, oid: UUID) -> StoredObject | None:
        query = select(StoredObjectORM).where(StoredObjectORM.oid == oid)
        cursor = await self._session.execute(query)
        row = cursor.scalar_one_or_none()
        return self._mapper.to_entity(row) if row else None

    async def delete(self, oid: UUID) -> None:
        query = delete(StoredObjectORM).where(StoredObjectORM.oid == oid)
        await self._session.execute(query)

    async def get_many(self, limit: int = 100, offset: int = 0) -> list[StoredObject]:
        query = select(StoredObjectORM).limit(limit).offset(offset)
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()
        return [self._mapper.to_entity(row) for row in rows]
