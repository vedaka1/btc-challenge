from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_challenge.users.adapters.sqlite.mapper import SqliteUserMapper
from btc_challenge.users.adapters.sqlite.model import UserORM
from btc_challenge.users.domain.entity import User
from btc_challenge.users.domain.repository import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = SqliteUserMapper

    async def create(self, user: User) -> None:
        orm = self._mapper.to_model(user)
        self._session.add(orm)

    async def update(self, user: User) -> None:
        orm = self._mapper.to_model(user)
        await self._session.merge(orm)

    async def _get_by(self, query: Select[tuple[UserORM]]) -> User | None:
        cursor = await self._session.execute(query)
        row = cursor.scalar_one_or_none()
        return self._mapper.to_entity(row) if row else None

    async def get_by_oid(self, oid: UUID) -> User | None:
        query = select(UserORM).where(UserORM.oid == oid)
        return await self._get_by(query)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        query = select(UserORM).where(UserORM.telegram_id == telegram_id)
        return await self._get_by(query)

    async def get_many(
        self,
        oids: list[UUID] | None = None,
        is_verified: bool | None = True,
        begin_created_at: datetime | None = None,
        end_created_at: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]:
        query = select(UserORM)
        if oids is not None:
            if not oids:
                return []
            query = query.where(UserORM.oid.in_(oids))
        if is_verified is not None:
            query = query.where(UserORM.is_verified == is_verified)
        if begin_created_at:
            query = query.where(UserORM.created_at >= begin_created_at)
        if end_created_at:
            query = query.where(UserORM.created_at <= end_created_at)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        query = query.order_by(UserORM.created_at.desc())
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()
        return [self._mapper.to_entity(row) for row in rows]
