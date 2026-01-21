from dataclasses import dataclass
from uuid import uuid4

from btc_challenge.push_ups.domain.entity import PushUp
from btc_challenge.push_ups.domain.repository import IPushUpRepository
from btc_challenge.shared.application.commiter import ICommiter
from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.shared.storage import IS3Storage
from btc_challenge.stored_object.domain.entity import StoredObject
from btc_challenge.stored_object.domain.repository import IStoredObjectRepository
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class CreatePushUpInteractor:
    push_up_repository: IPushUpRepository
    stored_object_repository: IStoredObjectRepository
    user_repository: IUserRepository
    storage: IS3Storage
    commiter: ICommiter

    async def execute(
        self,
        telegram_id: int,
        file_data: bytes,
        file_name: str,
        extension: str,
        count: int = 0,
    ) -> PushUp:
        # Сохраняем видео в MinIO
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            msg = f"User with telegram_id {telegram_id} not found"
            raise ObjectNotFoundError(msg)

        # Создаем запись об объекте в БД
        storage_key = await self.storage.put_bytes(
            filename=f"{uuid4()}{extension}",
            data=file_data,
        )
        stored_object = StoredObject.create(
            file_name=file_name,
            storage_key=storage_key,
            size=len(file_data),
            extension=extension,
        )
        await self.stored_object_repository.create(stored_object)

        # Создаем запись о подходе
        push_up = PushUp.create(
            user_oid=user.oid,
            video_oid=stored_object.oid,
            count=count,
        )
        await self.push_up_repository.create(push_up)

        await self.commiter.commit()
        return push_up
