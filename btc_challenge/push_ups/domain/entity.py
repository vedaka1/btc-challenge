from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class PushUp:
    oid: UUID
    user_oid: UUID
    telegram_file_id: str
    is_video_note: bool
    count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, user_oid: UUID, telegram_file_id: str, is_video_note: bool, count: int = 0) -> "PushUp":
        now = datetime.now()
        return cls(
            oid=uuid4(),
            user_oid=user_oid,
            telegram_file_id=telegram_file_id,
            is_video_note=is_video_note,
            count=count,
            created_at=now,
            updated_at=now,
        )
