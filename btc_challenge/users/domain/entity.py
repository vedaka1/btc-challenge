from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class User:
    oid: UUID
    telegram_id: int
    username: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, telegram_id: int, username: str) -> "User":
        now = datetime.now()
        return cls(
            oid=uuid4(),
            telegram_id=telegram_id,
            username=username,
            created_at=now,
            updated_at=now,
        )
