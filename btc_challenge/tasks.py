import asyncio

from aiogram import Bot

from btc_challenge.shared.tasks.daily_notification import daily_notification_task
from btc_challenge.shared.tasks.event_daily_notification import event_daily_notification_task
from btc_challenge.shared.tasks.event_notification import event_notification_task


def init_tasks(bot: Bot) -> None:
    tasks = [
        daily_notification_task(bot),
        event_notification_task(bot),
        event_daily_notification_task(bot),
    ]
    for task in tasks:
        asyncio.create_task(task)
