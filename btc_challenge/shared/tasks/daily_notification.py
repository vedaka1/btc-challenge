import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot

from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.push_ups.adapters.sqlite.repository import PushUpRepository
from btc_challenge.push_ups.application.interactors.get_all_users_stats_by_date import (
    GetAllUsersStatsByDateInteractor,
)
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.shared.providers import DatetimeProvider
from btc_challenge.shared.tasks.send_to_groups import send_notification_to_groups
from btc_challenge.users.adapters.sqlite.repository import UserRepository

logger = logging.getLogger(__name__)


async def send_daily_notification(bot: Bot, target_date: datetime) -> None:
    """Send daily stats report to groups."""
    async with get_async_session() as session:
        # Get stats for the target date
        interactor = GetAllUsersStatsByDateInteractor(
            push_up_repository=PushUpRepository(session),
            user_repository=UserRepository(session),
        )
        stats_list = await interactor.execute(date=target_date)
        if not stats_list:
            return

        date_str = target_date.strftime('%d.%m.%Y')

        # Подсчитываем общее количество отжиманий за день
        total_pushups = sum(stats.total_count for stats in stats_list)

        # Получаем текущий активный ивент
        event_repository = EventRepository(session)
        active_event = await event_repository.get_current_active_event()

        # Получаем статистику с начала ивента, если есть активный ивент
        event_stats = {}
        total_event_pushups = 0
        if active_event:
            user_repository = UserRepository(session)
            all_users = await user_repository.get_many(is_verified=True)
            user_oids = [user.oid for user in all_users]

            # Получаем все отжимания с начала ивента до конца текущего дня
            event_begin = active_event.start_at.replace(hour=0, minute=0, second=0, microsecond=0)
            event_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            push_up_repository = PushUpRepository(session)
            all_event_pushups = await push_up_repository.get_by_user_oids_and_date(
                user_oids=user_oids,
                begin_date=event_begin,
                end_date=event_end,
            )

            # Группируем по пользователям
            user_map = {user.oid: user for user in all_users}
            for push_up in all_event_pushups:
                user = user_map.get(push_up.user_oid)
                if user:
                    if user.username not in event_stats:
                        event_stats[user.username] = 0
                    event_stats[user.username] += push_up.count
                    total_event_pushups += push_up.count

        # Получаем список тех, кто не выполнил отжимания
        user_repository = UserRepository(session)
        all_users = await user_repository.get_many(is_verified=True)
        participant_usernames = {stats.username for stats in stats_list}
        inactive_users = [user.username for user in all_users if user.username not in participant_usernames]

        # Формируем текст с рейтингом
        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        stats_text = f'🏆 Отчет за {date_str}:\n\n'
        stats_text += f'💪 Всего за день: {total_pushups}\n'
        if active_event:
            stats_text += f'🔥 Всего с начала ивента: {total_event_pushups}\n'
        stats_text += '\n'

        for idx, stats in enumerate(stats_list, start=1):
            medal = medals.get(idx, f'{idx}.')
            event_info = ''
            if active_event and stats.username in event_stats:
                event_info = f' (всего в ивенте: {event_stats[stats.username]})'
            stats_text += (
                f'{medal} @{stats.username}\n'
                f'Отжиманий: {stats.total_count} ({stats.push_ups_count} подходов){event_info}\n\n'
            )

        # Добавляем список неактивных
        if inactive_users:
            stats_text += '❌ Не выполнили отжимания:\n'
            for username in inactive_users:
                stats_text += f'@{username}\n'

        # Send report to groups
        await send_notification_to_groups(bot, session, stats_text)

        await session.commit()


async def daily_notification_task(bot: Bot) -> None:
    """Background task to send daily report at 00:05."""
    while True:
        try:
            # Calculate next 00:05 UTC
            now = DatetimeProvider.provide()
            next_notification_time = now.replace(hour=21, minute=5, second=0, microsecond=0)
            if now >= next_notification_time:
                next_notification_time += timedelta(days=1)

            sleep_time = (next_notification_time - now).total_seconds()
            logger.info('Next daily notification at %s in %s seconds', next_notification_time, sleep_time)
            await asyncio.sleep(sleep_time)

            # Send report for previous day
            target_date = DatetimeProvider.provide()
            logger.info('Sending daily notification for %s', target_date.strftime('%d.%m.%Y'))
            await send_daily_notification(bot, target_date)
        except Exception as e:
            logger.error('Error in daily_notification_task: %s', e)
            await asyncio.sleep(60)
