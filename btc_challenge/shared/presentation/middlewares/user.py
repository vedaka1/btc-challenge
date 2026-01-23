from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser
from punq import Container

from btc_challenge.shared.errors import ObjectAlreadyExistsError, ObjectNotFoundError
from btc_challenge.users.application.interactors.create import CreateUserInteractor
from btc_challenge.users.application.interactors.get_one import GetUserByTelegramIdInteractor


class UserMiddleware(BaseMiddleware):
    """Middleware that ensures user exists and loads user entity into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TelegramUser | None = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        if not tg_user.username:
            msg = "Telegram username not specified"
            raise Exception(msg)

        container: Container = data["container"]

        # Ensure user exists in database
        create_interactor: CreateUserInteractor = container.resolve(CreateUserInteractor)
        try:
            await create_interactor.execute(tg_user.id, tg_user.username)
        except ObjectAlreadyExistsError:
            pass

        # Load user entity and add to data
        get_user_interactor: GetUserByTelegramIdInteractor = container.resolve(
            GetUserByTelegramIdInteractor,
        )
        try:
            user = await get_user_interactor.execute(tg_user.id)
            data["user"] = user
        except ObjectNotFoundError:
            # User should exist after creation, but handle edge case
            data["user"] = None

        return await handler(event, data)
