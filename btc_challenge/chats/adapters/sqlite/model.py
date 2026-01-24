from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.models import BaseORM


class ChatORM(BaseORM):
    __tablename__ = "chats"

    oid: Mapped[UUID] = mapped_column(primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(unique=True)
    chat_type: Mapped[str]
    title: Mapped[str | None]
    is_active: Mapped[bool]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
