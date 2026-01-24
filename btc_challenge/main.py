import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from btc_challenge.chats.presentation.router import chats_router
from btc_challenge.config import AppConfig
from btc_challenge.container import build_container
from btc_challenge.events.presentation.router import events_router
from btc_challenge.push_ups.presentation.router import logger, push_ups_router
from btc_challenge.shared.adapters.sqlite.session import get_async_engine
from btc_challenge.shared.presentation.commands import Commands
from btc_challenge.shared.presentation.middlewares.container import ContainerMiddleware
from btc_challenge.shared.presentation.middlewares.user import UserMiddleware
from btc_challenge.tasks import init_tasks
from btc_challenge.users.presentation.router import user_router
from btc_challenge.users.presentation.verification_router import verification_router


def init_routers(dp: Dispatcher):
    # Global middlewares - apply to all handlers
    dp.message.middleware(ContainerMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(ContainerMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.my_chat_member.middleware(ContainerMiddleware())

    # Routers
    dp.include_router(user_router)
    dp.include_router(verification_router)
    dp.include_router(push_ups_router)
    dp.include_router(events_router)
    dp.include_router(chats_router)


def init_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def main() -> None:
    init_logger()
    bot = Bot(token=AppConfig.telegram.bot_token)
    await bot.set_my_commands(
        commands=[
            BotCommand(command=Commands.START, description="Начать работу с ботом"),
            BotCommand(command=Commands.ADD, description="Добавить отжимания"),
            BotCommand(command=Commands.INFO, description="Моя статистика за сегодня"),
            BotCommand(command=Commands.STATS, description="Рейтинг всех пользователей"),
            BotCommand(command=Commands.HISTORY, description="Посмотреть историю по дням"),
            BotCommand(command=Commands.CANCEL, description="Отменить текущее действие"),
            BotCommand(command=Commands.ACTIVE_EVENTS, description="Посмотреть активные ивенты"),
            BotCommand(command=Commands.CONFIRMATION, description="Верификация пользователя"),
        ],
    )
    dp = Dispatcher()
    container = build_container()
    dp["container"] = container
    init_routers(dp)
    init_tasks(bot)
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by KeyboardInterrupt")
        await dp.stop_polling()
        engine = get_async_engine()
        await engine.dispose()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
