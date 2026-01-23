from uuid import UUID

from btc_challenge.events.adapters.sqlite.model import EventORM
from btc_challenge.events.domain.entity import Event


class EventMapper:
    @staticmethod
    def to_domain(event_orm: EventORM, participant_oids: list[UUID]) -> Event:
        return Event(
            oid=event_orm.oid,
            creator_oid=event_orm.creator_oid,
            title=event_orm.title,
            description=event_orm.description,
            start_at=event_orm.start_at,
            end_at=event_orm.end_at,
            initial_notification_sent=event_orm.initial_notification_sent,
            reminder_notification_sent=event_orm.reminder_notification_sent,
            start_notification_sent=event_orm.start_notification_sent,
            participant_oids=participant_oids,
            created_at=event_orm.created_at,
            updated_at=event_orm.updated_at,
        )

    @staticmethod
    def to_orm(event: Event) -> EventORM:
        return EventORM(
            oid=event.oid,
            creator_oid=event.creator_oid,
            title=event.title,
            description=event.description,
            start_at=event.start_at,
            end_at=event.end_at,
            initial_notification_sent=event.initial_notification_sent,
            reminder_notification_sent=event.reminder_notification_sent,
            start_notification_sent=event.start_notification_sent,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )
