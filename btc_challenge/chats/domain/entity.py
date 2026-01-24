from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Chat:
    oid: UUID
    telegram_chat_id: int
    chat_type: str  # 'group' or 'supergroup'
    title: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, telegram_chat_id: int, chat_type: str, title: str | None = None) -> "Chat":
        now = datetime.now()
        return cls(
            oid=uuid4(),
            telegram_chat_id=telegram_chat_id,
            chat_type=chat_type,
            title=title,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now()
