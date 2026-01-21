import asyncio

from aiogram import Bot

from btc_challenge.shared.tasks.daily_notification import daily_notification_task


def init_tasks(bot: Bot) -> None:
    tasks = [
        daily_notification_task(bot),
    ]
    for task in tasks:
        asyncio.create_task(task)
