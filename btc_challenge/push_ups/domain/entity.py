from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class PushUp:
    oid: UUID
    user_oid: UUID
    video_oid: UUID
    count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, user_oid: UUID, video_oid: UUID, count: int = 0) -> "PushUp":
        now = datetime.now()
        return cls(
            oid=uuid4(),
            user_oid=user_oid,
            video_oid=video_oid,
            count=count,
            created_at=now,
            updated_at=now,
        )
