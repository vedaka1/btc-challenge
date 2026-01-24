from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from btc_challenge.events.domain.entity import Event


class IEventRepository(ABC):
    @abstractmethod
    async def create(self, event: Event) -> Event:
        pass

    @abstractmethod
    async def save(self, event: Event) -> Event:
        pass

    @abstractmethod
    async def get_by_oid(self, oid: UUID) -> Event:
        pass

    @abstractmethod
    async def add_participant(self, event_oid: UUID, user_oid: UUID) -> None:
        pass

    @abstractmethod
    async def get_events_starting_soon(
        self, window_start: datetime, window_end: datetime
    ) -> list[Event]:
        pass

    @abstractmethod
    async def get_events_starting_now(self, now: datetime) -> list[Event]:
        pass

    @abstractmethod
    async def get_active_events(self, now: datetime) -> list[Event]:
        pass

    @abstractmethod
    async def get_active_events_by_participant(self, participant_oid: UUID, now: datetime) -> list[Event]:
        pass

    @abstractmethod
    async def get_current_active_event(self) -> Event | None:
        pass

    @abstractmethod
    async def has_active_event(self) -> bool:
        pass

    @abstractmethod
    async def get_uncompleted_events(self) -> list[Event]:
        pass
