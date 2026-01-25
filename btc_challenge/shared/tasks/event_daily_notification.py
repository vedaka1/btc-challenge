import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.events.domain.entity import Event
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.shared.tasks.send_to_groups import send_notification_to_groups
from btc_challenge.shared.utils import create_event_notification_text
from btc_challenge.users.adapters.sqlite.repository import UserRepository
from btc_challenge.users.domain.repository import IUserRepository


async def send_event_daily_notification_to_participant(
    bot: Bot,
    event: Event,
    user_repository: IUserRepository,
) -> None:
    participants = await user_repository.get_many(oids=event.participant_oids)
    notification_text = create_event_notification_text(event)
    for participant in participants:
        try:
            await bot.send_message(
                chat_id=participant.telegram_id,
                text=notification_text,
            )
        except Exception:
            pass


async def send_event_daily_notification(bot: Bot) -> None:
    """Send daily notification to event participants and groups at 5:00 about required pushups."""
    now = datetime.now()

    async with get_async_session() as session:
        event_repository = EventRepository(session)
        user_repository = UserRepository(session)

        active_events = await event_repository.get_active_events(now)
        for event in active_events:
            if not event.participant_oids:
                continue

            # Send to participants
            await send_event_daily_notification_to_participant(bot, event, user_repository)

            # Send to groups
            notification_text = create_event_notification_text(event)
            await send_notification_to_groups(bot, session, notification_text)
            await session.commit()


async def event_daily_notification_task(bot: Bot) -> None:
    """Background task to send daily notifications to event participants at 5:00."""
    while True:
        await send_event_daily_notification(bot)
        now = datetime.now()
        now.replace(hour=2, minute=0, second=0, microsecond=0)
        next_notification_time = now + timedelta(days=1)
        sleep_seconds = (next_notification_time - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
