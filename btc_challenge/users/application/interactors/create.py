from dataclasses import dataclass

from btc_challenge.shared.application.commiter import ICommiter
from btc_challenge.users.domain.entity import User
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class CreateUserInteractor:
    user_repository: IUserRepository
    commiter: ICommiter

    async def execute(self, user_id: int, username: str) -> User:
        if user_id <= 0:
            msg = "User id must be positive"
            raise ValueError(msg)

        if not username or not username.strip():
            msg = "Username cannot be empty"
            raise ValueError(msg)

        user = User.create(telegram_id=user_id, username=username)
        await self.user_repository.create(user)
        await self.commiter.commit()
        return user
