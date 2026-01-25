import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot

from btc_challenge.push_ups.adapters.sqlite.repository import PushUpRepository
from btc_challenge.push_ups.application.interactors.get_all_users_stats_by_date import (
    GetAllUsersStatsByDateInteractor,
)
from btc_challenge.shared.adapters.sqlite.session import get_async_session
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

        date_str = target_date.strftime("%d.%m.%Y")

        # Подсчитываем общее количество отжиманий
        total_pushups = sum(stats.total_count for stats in stats_list)

        # Получаем список тех, кто не выполнил отжимания
        user_repository = UserRepository(session)
        all_users = await user_repository.get_many(is_verified=True)
        participant_usernames = {stats.username for stats in stats_list}
        inactive_users = [user.username for user in all_users if user.username not in participant_usernames]

        # Формируем текст с рейтингом
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        stats_text = f"🏆 Отчет за {date_str}:\n\n"
        stats_text += f"💪 Всего отжиманий: {total_pushups}\n\n"
        for idx, stats in enumerate(stats_list, start=1):
            medal = medals.get(idx, f"{idx}.")
            stats_text += (
                f"{medal} @{stats.username}\nОтжиманий: {stats.total_count} ({stats.push_ups_count} подходов)\n\n"
            )

        # Добавляем список неактивных
        if inactive_users:
            stats_text += "❌ Не выполнили отжимания:\n"
            for username in inactive_users:
                stats_text += f"@{username}\n"

        # Send report to groups
        await send_notification_to_groups(bot, session, stats_text)

        await session.commit()


async def daily_notification_task(bot: Bot) -> None:
    """Background task to send daily report at 00:05."""
    while True:
        try:
            # Calculate next 00:05 UTC
            now = datetime.now()
            next_notification_time = now.replace(hour=21, minute=5, second=0, microsecond=0)
            if now >= next_notification_time:
                next_notification_time += timedelta(days=1)

            sleep_time = (next_notification_time - now).total_seconds()
            logger.info("Next daily notification at %s in %s seconds", next_notification_time, sleep_time)
            await asyncio.sleep(sleep_time)

            # Send report for previous day
            target_date = datetime.now()
            logger.info("Sending daily notification for %s", target_date.strftime("%d.%m.%Y"))
            await send_daily_notification(bot, target_date)
        except Exception as e:
            logger.error("Error in daily_notification_task: %s", e)
            await asyncio.sleep(60)
