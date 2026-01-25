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
from btc_challenge.shared.utils import pluralize_pushups
from btc_challenge.users.adapters.sqlite.repository import UserRepository

logger = logging.getLogger(__name__)


async def send_daily_notification(bot: Bot, target_date: datetime) -> None:
    """Send daily stats report to all users who had pushups that day and to groups."""
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

        # Формируем текст с рейтингом
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        stats_text = f"🏆 Отчет за {date_str}:\n\n"
        for idx, stats in enumerate(stats_list, start=1):
            medal = medals.get(idx, f"{idx}.")
            stats_text += (
                f"{medal} @{stats.username}\nОтжиманий: {stats.total_count} ({stats.push_ups_count} подходов)\n\n"
            )

        # Get all users who participated
        user_repository = UserRepository(session)
        all_users = await user_repository.get_many(is_verified=True)

        # Send report to all users who had pushups
        participant_usernames = {stats.username for stats in stats_list}
        for user in all_users:
            if user.username in participant_usernames:
                try:
                    await bot.send_message(user.telegram_id, stats_text)

                    # Send videos using telegram file_id
                    for stats in stats_list:
                        if stats.videos:
                            await bot.send_message(user.telegram_id, f"📹 Видео @{stats.username}:")
                            for count, file_id, is_video_note in stats.videos:
                                if is_video_note:
                                    await bot.send_video_note(
                                        chat_id=user.telegram_id,
                                        video_note=file_id,
                                    )
                                    await bot.send_message(
                                        chat_id=user.telegram_id,
                                        text=f"@{stats.username}: {count} {pluralize_pushups(count)}",
                                    )
                                else:
                                    await bot.send_video(
                                        chat_id=user.telegram_id,
                                        video=file_id,
                                        caption=f"@{stats.username}: {count} {pluralize_pushups(count)}",
                                    )
                except Exception:
                    # User might have blocked the bot
                    pass

        # Send report to groups (text only, without videos)
        await send_notification_to_groups(bot, session, stats_text)

        await session.commit()


async def daily_notification_task(bot: Bot) -> None:
    """Background task to send daily report at 00:05."""
    while True:
        try:
            # Calculate next 00:05 UTC
            now = datetime.now()
            next_notification_time = now.replace(hour=0, minute=5, second=0, microsecond=0)
            if now >= next_notification_time:
                next_notification_time += timedelta(days=1)

            sleep_time = (next_notification_time - now).total_seconds()
            logger.info("Next daily notification at %s in %s seconds", next_notification_time, sleep_time)
            await asyncio.sleep(sleep_time)

            # Send report for previous day
            target_date = datetime.now() - timedelta(days=1)
            logger.info("Sending daily notification for %s", target_date.strftime("%d.%m.%Y"))
            await send_daily_notification(bot, target_date)
        except Exception as e:
            logger.error("Error in daily_notification_task: %s", e)
            await asyncio.sleep(60)
