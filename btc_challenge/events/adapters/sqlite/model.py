from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.mixins import DatetimeMixin, IdentityMixin
from btc_challenge.shared.adapters.sqlite.models import BaseORM


class EventORM(BaseORM, IdentityMixin, DatetimeMixin):
    __tablename__ = 'events'

    creator_oid: Mapped[UUID] = mapped_column(ForeignKey('users.oid'))
    title: Mapped[str]
    description: Mapped[str]
    start_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]
    reminder_notification_sent: Mapped[bool]
    start_notification_sent: Mapped[bool]


class EventParticipantORM(BaseORM):
    __tablename__ = 'event_participants'

    event_oid: Mapped[UUID] = mapped_column(ForeignKey('events.oid'), primary_key=True)
    user_oid: Mapped[UUID] = mapped_column(ForeignKey('users.oid'), primary_key=True)
    joined_at: Mapped[datetime]
