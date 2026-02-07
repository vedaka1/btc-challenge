from dataclasses import dataclass

from btc_challenge.push_ups.domain.repository import IPushUpRepository
from btc_challenge.shared.date import get_moscow_day_range
from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.users.domain.repository import IUserRepository


@dataclass
class DailyStats:
    total_count: int
    push_ups_count: int
    videos: list[tuple[int, str, bool]]  # (count, file_id, is_video_note)


@dataclass
class GetDailyStatsInteractor:
    push_up_repository: IPushUpRepository
    user_repository: IUserRepository

    async def execute(self, telegram_id: int) -> DailyStats:
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            msg = f'User with telegram_id {telegram_id} not found'
            raise ObjectNotFoundError(msg)

        # Получаем начало и конец сегодняшнего дня по Москве
        begin_date, end_date = get_moscow_day_range()

        # Получаем все подходы за сегодня
        push_ups = await self.push_up_repository.get_by_user_oid_and_date(
            user_oid=user.oid,
            begin_date=begin_date,
            end_date=end_date,
        )

        total_count = sum(p.count for p in push_ups)
        videos = [(p.count, p.telegram_file_id, p.is_video_note) for p in push_ups]

        return DailyStats(
            total_count=total_count,
            push_ups_count=len(push_ups),
            videos=videos,
        )
