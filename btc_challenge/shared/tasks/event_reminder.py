import asyncio
import logging
from collections import defaultdict
from datetime import timedelta
from uuid import UUID

from aiogram import Bot

from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.push_ups.adapters.sqlite.repository import PushUpRepository
from btc_challenge.push_ups.domain.entity import PushUp
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.shared.providers import DatetimeProvider
from btc_challenge.shared.utils import pluralize_pushups
from btc_challenge.users.adapters.sqlite.repository import UserRepository

logger = logging.getLogger(__name__)


async def send_pushup_reminder_to_inactive_participants(bot: Bot) -> None:
    """Send reminder at 17:00 UTC to participants who haven't uploaded pushups today."""
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        user_repository = UserRepository(session)
        push_up_repository = PushUpRepository(session)

        now = DatetimeProvider.provide()
        begin_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = begin_date + timedelta(days=1) - timedelta(microseconds=1)

        active_events = await event_repository.get_active_events(now)
        for event in active_events:
            if not event.participant_oids:
                continue

            # Get all participants
            participants = await user_repository.get_many(oids=event.participant_oids)
            participant_map = {p.oid: p for p in participants}

            # Get all pushups for all participants in one query
            all_pushups = await push_up_repository.get_by_user_oids_and_date(
                user_oids=event.participant_oids,
                begin_date=begin_date,
                end_date=end_date,
            )

            # Group pushups by user_oid
            pushups_by_user: dict[UUID, list[PushUp]] = defaultdict(list)
            for pushup in all_pushups:
                pushups_by_user[pushup.user_oid].append(pushup)

            # Check each participant
            required_count = event.day_number
            for participant_oid, participant in participant_map.items():
                pushups_today = pushups_by_user.get(participant_oid, [])
                has_completed = any(pushup.count == required_count for pushup in pushups_today)

                if not has_completed:
                    reminder_text = (
                        f'⏰ Напоминание!\n\n'
                        f'{event.str_info}\n\n'
                        f'Ты еще не загрузил {required_count} {pluralize_pushups(required_count)} за сегодня.\n'
                        f'Не забудь выполнить задание!'
                    )
                    try:
                        await bot.send_message(
                            chat_id=participant.telegram_id,
                            text=reminder_text,
                        )
                        logger.info('Sent reminder to %s', participant.username)
                    except Exception as e:
                        logger.warning('Failed to send reminder to %s: %s', participant.username, e)


async def event_reminder_task(bot: Bot) -> None:
    """Background task to send reminders at 17:00 UTC."""
    while True:
        try:
            # Calculate next 17:00 UTC
            now = DatetimeProvider.provide()
            next_reminder_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            if now >= next_reminder_time:
                next_reminder_time += timedelta(days=1)

            sleep_seconds = (next_reminder_time - now).total_seconds()
            logger.info('Next reminder at %s UTC, sleeping %ss', next_reminder_time, sleep_seconds)

            await asyncio.sleep(sleep_seconds)

            logger.info('Sending pushup reminders to inactive participants')
            await send_pushup_reminder_to_inactive_participants(bot)

        except Exception as e:
            logger.error('Error in event_reminder_task: %s', e)
            await asyncio.sleep(60)
