from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from btc_challenge.push_ups.domain.entity import PushUp
from btc_challenge.push_ups.domain.repository import IPushUpRepository
from btc_challenge.shared.date import to_moscow
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class UserDateStats:
    username: str
    total_count: int
    push_ups_count: int
    videos: list[tuple[int, str, bool]]  # (count, file_id, is_video_note)


@dataclass
class GetAllUsersStatsByDateInteractor:
    push_up_repository: IPushUpRepository
    user_repository: IUserRepository

    async def execute(self, date: datetime) -> list[UserDateStats]:
        # Получаем начало и конец выбранного дня
        begin_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Получаем всех пользователей
        users = await self.user_repository.get_many()
        if not users:
            return []

        # Получаем все подходы за выбранную дату одним запросом
        user_oids = [user.oid for user in users]
        all_push_ups = await self.push_up_repository.get_by_user_oids_and_date(
            user_oids=user_oids,
            begin_date=to_moscow(begin_date),
            end_date=to_moscow(end_date),
        )

        # Группируем подходы по пользователям
        user_push_ups: dict[UUID, list[PushUp]] = {user_oid: [] for user_oid in user_oids}
        for push_up in all_push_ups:
            user_push_ups[push_up.user_oid].append(push_up)

        # Формируем статистику
        stats_list: list[UserDateStats] = []
        user_map = {user.oid: user for user in users}
        for user_oid, push_ups in user_push_ups.items():
            if push_ups:  # Показываем только тех, у кого есть подходы
                user = user_map[user_oid]
                total_count = sum(p.count for p in push_ups)
                videos = [(p.count, p.telegram_file_id, p.is_video_note) for p in push_ups]

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
