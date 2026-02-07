from datetime import datetime, timedelta
from uuid import UUID

from btc_challenge.events.domain.entity import Event
from btc_challenge.events.domain.repository import IEventRepository
from btc_challenge.shared.application.commiter import ICommiter
from btc_challenge.shared.providers import DatetimeProvider


class CreateEventInteractor:
    def __init__(self, event_repository: IEventRepository, commiter: ICommiter):
        self._event_repository = event_repository
        self._commiter = commiter

    async def execute(
        self,
        creator_oid: UUID,
        title: str,
        description: str,
        start_at: datetime,
    ) -> Event:
        # Validate inputs
        if not title or not title.strip():
            msg = 'Title cannot be empty'
            raise ValueError(msg)

        if not description or not description.strip():
            msg = 'Description cannot be empty'
            raise ValueError(msg)

        # Validate start date
        now = DatetimeProvider.provide()
        min_start_time = now + timedelta(minutes=2)
        if start_at < min_start_time:
            msg = 'Дата начала должна быть минимум через 2 минуты'
            raise ValueError(msg)

        # Complete all uncompleted events before creating a new one
        uncompleted_events = await self._event_repository.get_uncompleted_events()
        for old_event in uncompleted_events:
            old_event.completed_at = now
            await self._event_repository.save(old_event)

        # Create new event
        event = Event.create(
            creator_oid=creator_oid,
            title=title,
            description=description,
            start_at=start_at,
        )
        await self._event_repository.create(event)
        await self._commiter.commit()
        return event
