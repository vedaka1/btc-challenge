from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from btc_challenge.push_ups.domain.entity import PushUp
from btc_challenge.push_ups.domain.repository import IPushUpRepository
from btc_challenge.shared.date import get_moscow_day_range
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class UserDailyStats:
    username: str
    total_count: int
    push_ups_count: int


@dataclass
class GetAllUsersStatsInteractor:
    push_up_repository: IPushUpRepository
    user_repository: IUserRepository

    async def execute(self, begin_date: datetime, end_date: datetime) -> list[UserDailyStats]:
        # Получаем всех пользователей
        users = await self.user_repository.get_many()
        if not users:
            return []

        # Получаем все подходы за сегодня одним запросом
        user_oids = [user.oid for user in users]
        all_push_ups = await self.push_up_repository.get_by_user_oids_and_date(
            user_oids=user_oids,
            begin_date=begin_date,
            end_date=end_date,
        )

        # Группируем подходы по пользователям
        user_push_ups: dict[UUID, list[PushUp]] = defaultdict(list)
        for push_up in all_push_ups:
            user_push_ups[push_up.user_oid].append(push_up)

        # Формируем статистику
        stats_list: list[UserDailyStats] = []
        user_map = {user.oid: user for user in users}
        for user_oid, push_ups in user_push_ups.items():
            if not push_ups:
                continue  # Показываем только тех, у кого есть подходы
            user = user_map[user_oid]
            total_count = sum(p.count for p in push_ups)
            stats_list.append(
                UserDailyStats(
                    username=user.username,
                    total_count=total_count,
                    push_ups_count=len(push_ups),
                ),
            )
        return stats_list
