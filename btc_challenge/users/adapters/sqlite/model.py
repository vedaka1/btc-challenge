from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.models import BaseORM


class UserORM(BaseORM):
    __tablename__ = "users"

    oid: Mapped[UUID] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
