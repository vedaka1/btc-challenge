from dataclasses import dataclass

from btc_challenge.push_ups.domain.entity import PushUp
from btc_challenge.push_ups.domain.repository import IPushUpRepository
from btc_challenge.shared.application.commiter import ICommiter
from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class CreatePushUpInteractor:
    push_up_repository: IPushUpRepository
    user_repository: IUserRepository
    commiter: ICommiter

    async def execute(
        self,
        telegram_id: int,
        telegram_file_id: str,
        is_video_note: bool,
        count: int = 0,
    ) -> PushUp:
        if count <= 0:
            msg = "Count must be greater than 0"
            raise ValueError(msg)

        if not telegram_file_id or not telegram_file_id.strip():
            msg = "Telegram file id cannot be empty"
            raise ValueError(msg)

        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            msg = f"User with telegram_id {telegram_id} not found"
            raise ObjectNotFoundError(msg)

        # Создаем запись о подходе
        push_up = PushUp.create(
            user_oid=user.oid,
            telegram_file_id=telegram_file_id,
            is_video_note=is_video_note,
            count=count,
        )
        await self.push_up_repository.create(push_up)

        await self.commiter.commit()
        return push_up
