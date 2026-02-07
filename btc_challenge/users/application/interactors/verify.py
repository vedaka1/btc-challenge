from dataclasses import dataclass

from btc_challenge.shared.application.commiter import ICommiter
from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.shared.providers import DatetimeProvider
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class VerifyUserInteractor:
    user_repository: IUserRepository
    commiter: ICommiter

    async def execute(self, telegram_id: int, is_verified: bool) -> None:
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            msg = f'User with telegram_id {telegram_id} not found'
            raise ObjectNotFoundError(msg)

        user.is_verified = is_verified
        user.updated_at = DatetimeProvider.provide()
        await self.user_repository.update(user)
        await self.commiter.commit()
