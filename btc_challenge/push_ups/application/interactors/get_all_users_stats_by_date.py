from dataclasses import dataclass
from datetime import datetime

from btc_challenge.push_ups.domain.repository import IPushUpRepository
from btc_challenge.shared.storage import IS3Storage
from btc_challenge.stored_object.domain.repository import IStoredObjectRepository
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class UserDateStats:
    username: str
    total_count: int
    push_ups_count: int
    videos: list[tuple[int, bytes]]  # (count, video_bytes)


@dataclass
class GetAllUsersStatsByDateInteractor:
    push_up_repository: IPushUpRepository
    stored_object_repository: IStoredObjectRepository
    user_repository: IUserRepository
    storage: IS3Storage

    async def execute(self, date: datetime) -> list[UserDateStats]:
        # Получаем начало и конец выбранного дня
        begin_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Получаем всех пользователей
        users = await self.user_repository.get_many()

        stats_list: list[UserDateStats] = []
        for user in users:
            # Получаем все подходы пользователя за выбранную дату
            push_ups = await self.push_up_repository.get_by_user_oid_and_date(
                user_oid=user.oid,
                begin_date=begin_date,
                end_date=end_date,
            )

            if push_ups:  # Показываем только тех, у кого есть подходы
                total_count = sum(p.count for p in push_ups)
                videos = []

                # Получаем видео для каждого подхода
                for push_up in push_ups:
                    stored_object = await self.stored_object_repository.get_by_oid(push_up.video_oid)
                    if stored_object:
                        video_bytes = await self.storage.get_bytes(stored_object.storage_key)
                        if video_bytes:
                            videos.append((push_up.count, video_bytes))

                stats_list.append(
                    UserDateStats(
                        username=user.username,
                        total_count=total_count,
                        push_ups_count=len(push_ups),
                        videos=videos,
                    ),
                )

        # Сортируем по убыванию количества отжиманий
        stats_list.sort(key=lambda x: x.total_count, reverse=True)
        return stats_list
