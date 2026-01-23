from datetime import datetime
from uuid import UUID

from btc_challenge.events.domain.entity import Event
from btc_challenge.events.domain.repository import IEventRepository
from btc_challenge.shared.application.commiter import ICommiter


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
        end_at: datetime,
    ) -> Event:
        # Validate dates
        now = datetime.now()
        if start_at <= now:
            raise ValueError("Event start time must be in the future")
        if end_at <= start_at:
            raise ValueError("Event end time must be after start time")

        event = Event.create(
            creator_oid=creator_oid,
            title=title,
            description=description,
            start_at=start_at,
            end_at=end_at,
        )
        await self._event_repository.create(event)
        await self._commiter.commit()
        return event
