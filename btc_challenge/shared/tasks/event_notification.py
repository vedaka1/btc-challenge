import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.events.domain.entity import Event
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.shared.tasks.event_daily_notification import (
    send_event_daily_notification_to_participant,
)
from btc_challenge.shared.tasks.send_to_groups import send_notification_to_groups
from btc_challenge.shared.utils import create_event_notification_text
from btc_challenge.users.adapters.sqlite.repository import UserRepository

logger = logging.getLogger(__name__)


async def send_pre_event_reminders(bot: Bot, event: Event) -> None:
    """Send reminder 1 hour before event to users who haven't joined yet and to all groups."""
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        user_repository = UserRepository(session)

        # Get all verified users
        all_users = await user_repository.get_many(is_verified=True)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Участвую", callback_data=f"join_event:{event.oid}")],
            ],
        )

        reminder_text = (
            f"⏰ Напоминание: ивент скоро начнется!\n\n"
            f"📌 {event.title}\n"
            f"📝 {event.description}\n"
            f"🕐 Начало: {event.start_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Успей записаться, до начала остался 1 час!"
        )

        # Send to verified users who are not participants
        for user in all_users:
            if user.oid not in event.participant_oids:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=reminder_text,
                        reply_markup=keyboard,
                    )
                except Exception:
                    # User might have blocked the bot
                    pass

        # Send to active chats (groups)
        await send_notification_to_groups(bot, session, reminder_text, keyboard)

        # Mark reminder notification as sent
        event.reminder_notification_sent = True
        await event_repository.save(event)
        await session.commit()


async def send_start_notification(bot: Bot, event: Event) -> None:
    """Send event start notification to all participants and active chats with participant list."""
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        user_repository = UserRepository(session)

        # Load participant users by their oids in single query
        participants = await user_repository.get_many(oids=event.participant_oids) if event.participant_oids else []

        # Create participant list
        participant_list = (
            "\n".join([f"• @{user.username}" for user in participants]) if participants else "Нет участников"
        )

        notification_text = (
            f"🎬 Ивент начинается!\n\n"
            f"📌 {event.title}\n"
            f"📝 {event.description}\n\n"
            f"👥 Участников: {len(participants)}\n{participant_list}"
        )

        # Send to all participants
        for participant in participants:
            try:
                await bot.send_message(
                    chat_id=participant.telegram_id,
                    text=notification_text,
                )
            except Exception:
                # User might have blocked the bot
                pass
        await send_notification_to_groups(bot, session, notification_text)

        # Mark start notification as sent
        event.start_notification_sent = True
        await event_repository.save(event)
        await session.commit()
        await send_event_daily_notification_to_participant(bot, event, user_repository)

        reminder_text = create_event_notification_text(event)
        await send_notification_to_groups(bot, session, reminder_text)


async def event_notification_task(bot: Bot) -> None:
    """Background task to send event notifications."""
    while True:
        try:
            now = datetime.now()
            async with get_async_session() as session:
                event_repository = EventRepository(session)

                # Check for events starting in 1 hour (with 2-minute window)
                one_hour_later = now + timedelta(hours=1)
                one_hour_later_end = one_hour_later + timedelta(minutes=2)
                logger.info(
                    f"Checking for events starting in 1 hour (with 2-minute window): {one_hour_later} - {one_hour_later_end}",
                )
                events_starting_soon = await event_repository.get_events_starting_soon(
                    one_hour_later,
                    one_hour_later_end,
                )

                for event in events_starting_soon:
                    if not event.reminder_notification_sent:
                        await send_pre_event_reminders(bot, event)

                not_started_events = await event_repository.get_events_starting_now(now)
                logger.info(f"{not_started_events}")
                for event in not_started_events:
                    logger.info(f"Sending start notification for event: {event.title}")
                    if not event.is_started:
                        await send_start_notification(bot, event)
            await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            # Log error but keep the task running
            logger.error(f"Error in event_notification_task: {e}")
            continue
