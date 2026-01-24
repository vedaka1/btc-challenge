from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_challenge.chats.adapters.sqlite.mapper import SqliteChatMapper
from btc_challenge.chats.adapters.sqlite.model import ChatORM
from btc_challenge.chats.domain.entity import Chat
from btc_challenge.chats.domain.repository import IChatRepository


class ChatRepository(IChatRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = SqliteChatMapper

    async def create(self, chat: Chat) -> None:
        orm = self._mapper.to_model(chat)
        self._session.add(orm)

    async def update(self, chat: Chat) -> None:
        orm = self._mapper.to_model(chat)
        await self._session.merge(orm)

    async def _get_by(self, query: Select[tuple[ChatORM]]) -> Chat | None:
        cursor = await self._session.execute(query)
        row = cursor.scalar_one_or_none()
        return self._mapper.to_entity(row) if row else None

    async def get_by_oid(self, oid: UUID) -> Chat | None:
        query = select(ChatORM).where(ChatORM.oid == oid)
        return await self._get_by(query)

    async def get_by_telegram_chat_id(self, telegram_chat_id: int) -> Chat | None:
        query = select(ChatORM).where(ChatORM.telegram_chat_id == telegram_chat_id)
        return await self._get_by(query)

    async def get_many(self, is_active: bool | None = None) -> list[Chat]:
        query = select(ChatORM)
        if is_active is not None:
            query = query.where(ChatORM.is_active == is_active)
        query = query.order_by(ChatORM.created_at.desc())
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()
        return [self._mapper.to_entity(row) for row in rows]
