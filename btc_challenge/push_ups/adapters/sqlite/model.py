from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.models import BaseORM


class PushUpORM(BaseORM):
    __tablename__ = "push_up"

    oid: Mapped[UUID] = mapped_column(primary_key=True)
    user_oid: Mapped[UUID] = mapped_column(ForeignKey("users.oid", ondelete="CASCADE"), index=True)
    video_oid: Mapped[UUID] = mapped_column(ForeignKey("stored_object.oid", ondelete="CASCADE"))
    count: Mapped[int]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
