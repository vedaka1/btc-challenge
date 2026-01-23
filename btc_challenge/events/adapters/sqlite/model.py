from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.models import BaseORM


class EventORM(BaseORM):
    __tablename__ = "events"

    oid: Mapped[UUID] = mapped_column(primary_key=True)
    creator_oid: Mapped[UUID] = mapped_column(ForeignKey("users.oid"))
    title: Mapped[str]
    description: Mapped[str]
    start_at: Mapped[datetime]
    end_at: Mapped[datetime]
    initial_notification_sent: Mapped[bool]
    reminder_notification_sent: Mapped[bool]
    start_notification_sent: Mapped[bool]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class EventParticipantORM(BaseORM):
    __tablename__ = "event_participants"

    event_oid: Mapped[UUID] = mapped_column(ForeignKey("events.oid"), primary_key=True)
    user_oid: Mapped[UUID] = mapped_column(ForeignKey("users.oid"), primary_key=True)
    joined_at: Mapped[datetime]
