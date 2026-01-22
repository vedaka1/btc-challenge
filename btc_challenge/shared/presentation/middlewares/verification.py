from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from punq import Container

from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.users.application.interactors.get_one import GetUserByTelegramIdInteractor


class VerificationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data["event_from_user"]
        container: Container = data["container"]
        get_user_interactor: GetUserByTelegramIdInteractor = container.resolve(GetUserByTelegramIdInteractor)

        try:
            user = await get_user_interactor.execute(tg_user.id)
        except ObjectNotFoundError:
            await event.answer("Сначала нажми /start")
            return None

        if not user.is_verified:
            await event.answer("Ты не верифицирован! Отправь команду /confirmation для верификации.")
            return None

        return await handler(event, data)
