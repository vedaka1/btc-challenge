from datetime import datetime
from uuid import UUID

from btc_challenge.events.domain.repository import IEventRepository
from btc_challenge.shared.application.commiter import ICommiter


class JoinEventInteractor:
    def __init__(self, event_repository: IEventRepository, commiter: ICommiter):
        self._event_repository = event_repository
        self._commiter = commiter

    async def execute(self, event_oid: UUID, user_oid: UUID) -> None:
        # Check if event exists
        event = await self._event_repository.get_by_oid(event_oid)

        # Check if event hasn't started yet
        now = datetime.now()
        if event.start_at <= now:
            raise ValueError("Cannot join event that has already started")

        # Check if user is already a participant (using value object)
        if user_oid in event.participant_oids:
            raise ValueError("User is already a participant")

        await self._event_repository.add_participant(event_oid, user_oid)
        await self._commiter.commit()
