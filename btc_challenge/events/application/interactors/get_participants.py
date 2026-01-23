from uuid import UUID

from btc_challenge.events.domain.repository import IEventRepository
from btc_challenge.users.domain.entity import User
from btc_challenge.users.domain.repository import IUserRepository


class GetEventParticipantsInteractor:
    def __init__(
        self,
        event_repository: IEventRepository,
        user_repository: IUserRepository,
    ):
        self._event_repository = event_repository
        self._user_repository = user_repository

    async def execute(self, event_oid: UUID) -> list[User]:
        # Get event with participant_oids
        event = await self._event_repository.get_by_oid(event_oid)

        # Load users by their oids in single query
        return await self._user_repository.get_many(oids=event.participant_oids)
