from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.mixins import DatetimeMixin, IdentityMixin
from btc_challenge.shared.adapters.sqlite.models import BaseORM


class PushUpORM(BaseORM, IdentityMixin, DatetimeMixin):
    __tablename__ = 'push_up'

    user_oid: Mapped[UUID] = mapped_column(ForeignKey('users.oid', ondelete='CASCADE'), index=True)
    telegram_file_id: Mapped[str]
    is_video_note: Mapped[bool]
    count: Mapped[int]
