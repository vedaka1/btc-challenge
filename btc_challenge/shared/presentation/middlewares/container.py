from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from btc_challenge.container import build_request_container
from btc_challenge.shared.adapters.sqlite.session import get_async_session


class ContainerMiddleware(BaseMiddleware):
    """Middleware for injecting DI container into handlers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with get_async_session() as session:
            build_request_container(data["container"], session)
            return await handler(event, data)
