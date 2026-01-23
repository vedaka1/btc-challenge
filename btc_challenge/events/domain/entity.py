from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Event:
    oid: UUID
    creator_oid: UUID
    title: str
    description: str
    start_at: datetime
    end_at: datetime
    initial_notification_sent: bool
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
        end_at: datetime,
    ) -> "Event":
        now = datetime.now()
        return cls(
            oid=uuid4(),
            creator_oid=creator_oid,
            title=title,
            description=description,
            start_at=start_at,
            end_at=end_at,
            initial_notification_sent=False,
            reminder_notification_sent=False,
            start_notification_sent=False,
            participant_oids=[],
            created_at=now,
            updated_at=now,
        )

    @property
    def day_number(self) -> int:
        return (datetime.now().date() - self.start_at.date()).days + 1
