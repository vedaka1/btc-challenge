from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from btc_challenge.events.adapters.sqlite.mapper import EventMapper
from btc_challenge.events.adapters.sqlite.model import EventORM, EventParticipantORM
from btc_challenge.events.domain.entity import Event
from btc_challenge.events.domain.repository import IEventRepository
from btc_challenge.shared.errors import ObjectNotFoundError


class EventRepository(IEventRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = EventMapper

    async def create(self, event: Event) -> Event:
        orm = self._mapper.to_orm(event)
        self._session.add(orm)
        return event

    async def save(self, event: Event) -> Event:
        orm = self._mapper.to_orm(event)
        await self._session.merge(orm)
        return event

    async def _load_participants(self, event_oid: UUID) -> list[UUID]:
        """Load participant OIDs for an event."""
        query = select(EventParticipantORM.user_oid).where(
            EventParticipantORM.event_oid == event_oid,
        )
        cursor = await self._session.execute(query)
        return list(cursor.scalars().all())

    async def _get_by(self, query: Select[tuple[EventORM]]) -> Event | None:
        cursor = await self._session.execute(query)
        row = cursor.scalar_one_or_none()
        if not row:
            return None
        participant_oids = await self._load_participants(row.oid)
        return self._mapper.to_domain(row, participant_oids)

    async def get_by_oid(self, oid: UUID) -> Event:
        query = select(EventORM).where(EventORM.oid == oid)
        event = await self._get_by(query)
        if not event:
            raise ObjectNotFoundError(f"Event with oid {oid} not found")
        return event

    async def get_upcoming(self, now: datetime) -> list[Event]:
        query = select(EventORM).where(EventORM.start_at > now).order_by(EventORM.start_at)
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()

        events = []
        for row in rows:
            participant_oids = await self._load_participants(row.oid)
            events.append(self._mapper.to_domain(row, participant_oids))
        return events

    async def add_participant(self, event_oid: UUID, user_oid: UUID) -> None:
        participant = EventParticipantORM(
            event_oid=event_oid,
            user_oid=user_oid,
            joined_at=datetime.now(),
        )
        self._session.add(participant)

    async def get_events_starting_soon(
        self,
        window_start: datetime,
        window_end: datetime,
    ) -> list[Event]:
        query = (
            select(EventORM)
            .where(
                EventORM.start_at >= window_start,
                EventORM.start_at <= window_end,
                EventORM.reminder_notification_sent == False,
            )
            .order_by(EventORM.start_at)
        )
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()

        events = []
        for row in rows:
            participant_oids = await self._load_participants(row.oid)
            events.append(self._mapper.to_domain(row, participant_oids))
        return events

    async def get_events_starting_now(self, now: datetime, tolerance_seconds: int = 60) -> list[Event]:
        query = (
            select(EventORM)
            .where(
                EventORM.start_at >= now,
                EventORM.start_at <= datetime.fromtimestamp(now.timestamp() + tolerance_seconds),
                EventORM.start_notification_sent == False,
            )
            .order_by(EventORM.start_at)
        )
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()

        events = []
        for row in rows:
            participant_oids = await self._load_participants(row.oid)
            events.append(self._mapper.to_domain(row, participant_oids))
        return events

    async def get_active_events(self, now: datetime) -> list[Event]:
        """Get events that are currently active (start_at <= now <= end_at)."""
        query = (
            select(EventORM)
            .where(
                EventORM.start_at <= now,
                EventORM.end_at >= now,
            )
            .order_by(EventORM.start_at)
        )
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()

        events = []
        for row in rows:
            participant_oids = await self._load_participants(row.oid)
            events.append(self._mapper.to_domain(row, participant_oids))
        return events

    async def get_active_events_by_participant(self, participant_oid: UUID, now: datetime) -> list[Event]:
        """Get active events where user is a participant."""
        query = (
            select(EventORM)
            .join(EventParticipantORM, EventParticipantORM.event_oid == EventORM.oid)
            .where(
                EventORM.start_at <= now,
                EventORM.end_at >= now,
                EventParticipantORM.user_oid == participant_oid,
            )
            .order_by(EventORM.start_at)
        )
        cursor = await self._session.execute(query)
        rows = cursor.scalars().all()

        events = []
        for row in rows:
            participant_oids = await self._load_participants(row.oid)
            events.append(self._mapper.to_domain(row, participant_oids))
        return events
