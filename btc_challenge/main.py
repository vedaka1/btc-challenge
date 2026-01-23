import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from btc_challenge.config import AppConfig
from btc_challenge.container import build_container
from btc_challenge.events.presentation.router import events_router
from btc_challenge.push_ups.presentation.router import logger, push_ups_router
from btc_challenge.shared.adapters.sqlite.session import get_async_engine
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

    # Routers
    dp.include_router(user_router)
    dp.include_router(verification_router)
    dp.include_router(push_ups_router)
    dp.include_router(events_router)


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
            BotCommand(command="start", description="Начать работу с ботом"),
            BotCommand(command="add", description="Добавить отжимания"),
            BotCommand(command="info", description="Моя статистика за сегодня"),
            BotCommand(command="stats", description="Рейтинг всех пользователей"),
            BotCommand(command="history", description="Посмотреть историю по дням"),
            BotCommand(command="cancel", description="Отменить текущее действие"),
            BotCommand(command="confirmation", description="Верификация пользователя"),
        ],
    )
    dp = Dispatcher()
    container = build_container()
    dp["container"] = container
    init_routers(dp)
    init_tasks(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        engine = get_async_engine()
        engine.dispose()
        logger.info("Bot stopped")
