import asyncio
from collections import defaultdict
from datetime import datetime
from uuid import UUID

from aiogram import Bot

from btc_challenge.push_ups.adapters.sqlite.repository import PushUpRepository
from btc_challenge.push_ups.domain.entity import PushUp
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.users.adapters.sqlite.repository import UserRepository
from btc_challenge.users.domain.entity import User


async def send_daily_notification(
    bot: Bot,
    current_user: User,
    users: list[User],
    user_oid_to_push_ups_map: dict[UUID, list[PushUp]],
) -> None:
    push_ups = user_oid_to_push_ups_map.get(current_user.oid, [])
    if not push_ups:
        return

    text = "🎉 Отчет за сегодня:\n"
    for user in users:
        user_push_ups: list[PushUp] = user_oid_to_push_ups_map.get(user.oid, [])
        text += f"{user.username}: {sum(el.count for el in user_push_ups)}\n"
    text += f"\nОбщее количество отжиманий: {sum(el.count for el in push_ups)}"
    await bot.send_message(current_user.telegram_id, text)


async def daily_notification_task(bot: Bot) -> None:
    while True:
        now = datetime.now()
        next_notification_time = now.replace(day=now.day + 1, hour=10, minute=0, second=0, microsecond=0)
        await asyncio.sleep((next_notification_time - now).total_seconds())
        async with get_async_session() as session:
            begin_created_at = now.replace(hour=0, minute=0, second=0)
            end_created_at = now.replace(hour=23, minute=59, second=59)
            users = await UserRepository(session).get_many(
                begin_created_at=begin_created_at,
                end_created_at=end_created_at,
            )
            push_ups = await PushUpRepository(session).get_many(
                begin_created_at=begin_created_at,
                end_created_at=end_created_at,
            )

            user_oid_to_push_ups_map: dict[UUID, list[PushUp]] = defaultdict(list)
            for push_up in push_ups:
                user_oid_to_push_ups_map[push_up.user_oid].append(push_up)

            for user in users:
                await send_daily_notification(bot, user, users, user_oid_to_push_ups_map)
            break
