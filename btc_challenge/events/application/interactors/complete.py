from datetime import datetime
from uuid import UUID

from btc_challenge.events.domain.entity import Event
from btc_challenge.events.domain.repository import IEventRepository
from btc_challenge.shared.application.commiter import ICommiter


class CompleteEventInteractor:
    def __init__(self, event_repository: IEventRepository, commiter: ICommiter):
        self._event_repository = event_repository
        self._commiter = commiter

    async def execute(self, event_oid: UUID) -> Event:
        event = await self._event_repository.get_by_oid(event_oid)
        if not event:
            msg = "Event not found"
            raise ValueError(msg)

        if event.completed_at is not None:
            msg = "Ивент уже завершен"
            raise ValueError(msg)

        if not event.is_started:
            msg = "Нельзя завершить не начавшийся ивент"
            raise ValueError(msg)

        event.completed_at = datetime.now()
        await self._event_repository.save(event)
        await self._commiter.commit()
        return event
