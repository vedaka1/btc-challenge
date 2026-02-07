from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from btc_challenge.shared.date import to_moscow
from btc_challenge.shared.providers import DatetimeProvider, TimeZone


@dataclass
class Event:
    oid: UUID
    creator_oid: UUID
    title: str
    description: str
    start_at: datetime
    completed_at: datetime | None
    reminder_notification_sent: bool
    start_notification_sent: bool
    participant_oids: list[UUID]  # Value object - loaded with entity
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        creator_oid: UUID,
        title: str,
        description: str,
        start_at: datetime,
    ) -> 'Event':
        now = DatetimeProvider.provide()
        return cls(
            oid=uuid4(),
            creator_oid=creator_oid,
            title=title,
            description=description,
            start_at=start_at,
            completed_at=None,
            reminder_notification_sent=False,
            start_notification_sent=False,
            participant_oids=[],
            created_at=now,
            updated_at=now,
        )

    @property
    def day_number(self) -> int:
        return (to_moscow(DatetimeProvider.provide()).date() - to_moscow(self.start_at).date()).days + 1

    @property
    def is_started(self) -> bool:
        return DatetimeProvider.provide() >= self.start_at and self.start_notification_sent is True

    @property
    def is_active(self) -> bool:
        return self.is_started and self.completed_at is None

    @property
    def str_info(self) -> str:
        return f'📌 Ивент: {self.title}\n📅 День {self.day_number}'

    def get_day_number_by_date(self, current_date: datetime) -> int:
        return (
            current_date.astimezone(TimeZone.MOSCOW).date() - self.start_at.astimezone(TimeZone.MOSCOW).date()
        ).days + 1
