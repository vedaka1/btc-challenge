import asyncio

from aiogram import Bot, Dispatcher

from btc_challenge.config import AppConfig
from btc_challenge.container import build_container
from btc_challenge.push_ups.presentation.router import push_ups_router
from btc_challenge.shared.presentation.middlewares.container import ContainerMiddleware
from btc_challenge.shared.presentation.middlewares.user import UserMiddleware
from btc_challenge.shared.presentation.middlewares.verification import VerificationMiddleware
from btc_challenge.tasks import init_tasks
from btc_challenge.users.presentation.router import user_router
from btc_challenge.users.presentation.verification_router import verification_router


def init_routers(dp: Dispatcher):
    dp.message.middleware(ContainerMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(ContainerMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.include_router(user_router)
    dp.include_router(verification_router)

    # Apply verification middleware only to protected routers
    push_ups_router.message.middleware(VerificationMiddleware())
    dp.include_router(push_ups_router)


async def main() -> None:
    bot = Bot(token=AppConfig.telegram.bot_token)
    dp = Dispatcher()
    container = build_container()
    dp["container"] = container
    init_routers(dp)
    init_tasks(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
