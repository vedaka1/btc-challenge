import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.events.domain.entity import Event
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.users.adapters.sqlite.repository import UserRepository
from btc_challenge.users.domain.repository import IUserRepository


async def send_event_daily_notification_to_participant(
    bot: Bot,
    event: Event,
    user_repository: IUserRepository,
    now: datetime,
) -> None:
    day_number = event.day_number
    participants = await user_repository.get_many(oids=event.participant_oids)
    notification_text = (
        f"💪 Доброе утро!\n\n"
        f"📌 Ивент: {event.title}\n"
        f"📅 День {day_number}\n\n"
        f"Сегодня нужно сделать {day_number} отжиманий!"
    )

    for participant in participants:
        try:
            await bot.send_message(
                chat_id=participant.telegram_id,
                text=notification_text,
            )
        except Exception:
            pass


async def send_event_daily_notification(bot: Bot) -> None:
    """Send daily notification to event participants at 5:00 about required pushups."""
    now = datetime.now()

    async with get_async_session() as session:
        event_repository = EventRepository(session)
        user_repository = UserRepository(session)

        active_events = await event_repository.get_active_events(now)
        for event in active_events:
            if not event.participant_oids:
                continue
            await send_event_daily_notification_to_participant(bot, event, user_repository, now)


async def event_daily_notification_task(bot: Bot) -> None:
    """Background task to send daily notifications to event participants at 5:00."""
    while True:
        now = datetime.now()

        # Calculate next 5:00 AM
        next_notification_time = now.replace(hour=5, minute=0, second=0, microsecond=0)
        if now >= next_notification_time:
            # If it's already past 5:00 today, schedule for tomorrow
            next_notification_time = next_notification_time + timedelta(days=1)

        # Sleep until 5:00 AM
        sleep_seconds = (next_notification_time - now).total_seconds()
        await asyncio.sleep(sleep_seconds)

        await send_event_daily_notification(bot)
