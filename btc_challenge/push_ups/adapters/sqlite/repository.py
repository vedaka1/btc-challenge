from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_challenge.push_ups.adapters.sqlite.mapper import SqlitePushUpMapper
from btc_challenge.push_ups.adapters.sqlite.model import PushUpORM
from btc_challenge.push_ups.domain.entity import PushUp
from btc_challenge.push_ups.domain.repository import IPushUpRepository


class PushUpRepository(IPushUpRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = SqlitePushUpMapper

    async def create(self, push_up: PushUp) -> None:
        orm = self._mapper.to_model(push_up)
        self._session.add(orm)

    async def get_by_oid(self, push_up_oid: UUID) -> PushUp | None:
        query = select(PushUpORM).where(PushUpORM.oid == push_up_oid)
        cursor = await self._session.execute(query)
        row = cursor.scalar_one_or_none()
        return self._mapper.to_entity(row) if row else None

    async def get_by_user_oid(self, user_oid: UUID, limit: int = 100, offset: int = 0) -> list[PushUp]:
        query = select(PushUpORM).where(PushUpORM.user_oid == user_oid).limit(limit).offset(offset)
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()
        return [self._mapper.to_entity(row) for row in rows]

    async def get_by_user_oid_and_date(
        self,
        user_oid: UUID,
        begin_date: datetime,
        end_date: datetime,
    ) -> list[PushUp]:
        query = (
            select(PushUpORM)
            .where(PushUpORM.user_oid == user_oid)
            .where(PushUpORM.created_at >= begin_date)
            .where(PushUpORM.created_at <= end_date)
            .order_by(PushUpORM.created_at.desc())
        )
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()
        return [self._mapper.to_entity(row) for row in rows]

    async def get_many(
        self,
        begin_created_at: datetime | None = None,
        end_created_at: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[PushUp]:
        query = select(PushUpORM)
        if begin_created_at:
            query = query.where(PushUpORM.created_at >= begin_created_at)
        if end_created_at:
            query = query.where(PushUpORM.created_at <= end_created_at)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        query = query.order_by(PushUpORM.created_at.desc())
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()
        return [self._mapper.to_entity(row) for row in rows]
