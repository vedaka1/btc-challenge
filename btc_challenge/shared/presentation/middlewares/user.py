from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from punq import Container

from btc_challenge.shared.errors import ObjectAlreadyExistsError
from btc_challenge.users.application.interactors.create import CreateUserInteractor


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: User = data["event_from_user"]
        if not tg_user.username:
            msg = "Telegram username not specified"
            raise Exception(msg)

        container: Container = data["container"]
        interactor: CreateUserInteractor = container.resolve(CreateUserInteractor)
        try:
            await interactor.execute(tg_user.id, tg_user.username)
        except ObjectAlreadyExistsError:
            pass
        return await handler(event, data)
