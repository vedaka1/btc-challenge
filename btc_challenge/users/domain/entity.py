from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from btc_challenge.shared.providers import DatetimeProvider


@dataclass
class User:
    oid: UUID
    telegram_id: int
    username: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, telegram_id: int, username: str) -> 'User':
        now = DatetimeProvider.provide()
        return cls(
            oid=uuid4(),
            telegram_id=telegram_id,
            username=username,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
