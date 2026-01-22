from dataclasses import dataclass

from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.users.domain.entity import User
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class GetUserByTelegramIdInteractor:
    user_repository: IUserRepository

    async def execute(self, telegram_id: int) -> User:
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            msg = f"User with telegram_id {telegram_id} not found"
            raise ObjectNotFoundError(msg)
        return user
