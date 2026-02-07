from dataclasses import dataclass
from datetime import date

from btc_challenge.events.domain.entity import Event
from btc_challenge.events.domain.repository import IEventRepository
from btc_challenge.push_ups.domain.repository import IPushUpRepository
from btc_challenge.shared.date import get_moscow_day_range
from btc_challenge.shared.presentation.commands import Commands
from btc_challenge.shared.providers import DatetimeProvider, TimeZone
from btc_challenge.users.domain.entity import User


@dataclass
class CheckDailyPushUpsResult:
    count: int | None
    msg: str
    penalty_days: list[tuple[date, int]]
    active_event: Event | None
    today_count: int = 0


@dataclass(kw_only=True, slots=True, eq=False)
class CheckDailyPushUpsInteractor:
    event_repository: IEventRepository
    push_up_repository: IPushUpRepository

    async def execute(self, current_user: User) -> CheckDailyPushUpsResult:
        now = DatetimeProvider.provide()
        active_events = await self.event_repository.get_active_events_by_participant(current_user.oid, now)
        if not active_events:
            msg = str(
                f'❌ Ты не участвуешь ни в одном активном ивенте!\n\n'
                f'Используй /{Commands.ACTIVE_EVENTS} чтобы посмотреть доступные ивенты.',
            )
            return CheckDailyPushUpsResult(None, msg, [], None)

        # Используем day_number из активного события
        event = active_events[0]
        count = event.day_number

        missed_days = await self.push_up_repository.get_missed_days(
            user_oid=current_user.oid,
            event_started_at=event.start_at.astimezone(TimeZone.UTC),
        )
        missed_days_to_day_number: list[tuple[date, int]] = []
        for missed_day in missed_days:
            penalty = _calculate_penalty(event.get_day_number_by_date(missed_day))
            dto = (missed_day, penalty)
            missed_days_to_day_number.append(dto)

        begin_date, end_date = get_moscow_day_range()
        push_ups = await self.push_up_repository.get_by_user_oid_and_date(
            user_oid=current_user.oid,
            begin_date=begin_date,
            end_date=end_date,
        )
        if push_ups and not missed_days:
            msg = '❌ Ты уже отжимался сегодня'
            return CheckDailyPushUpsResult(None, msg, [], event, today_count=0)
        if not push_ups:
            msg = f'Отправь видео или кружок с отжиманиями: {count}'
            return CheckDailyPushUpsResult(count, msg, missed_days_to_day_number, event, today_count=count)

        penalty_count = sum(el[1] for el in missed_days_to_day_number)
        msg = (
            f'Отправь видео или кружок с отжиманиями: {penalty_count}\n'
            f'{count}+{penalty_count - count} штраф за пропуск'  # noqa
        )
        return CheckDailyPushUpsResult(penalty_count, msg, missed_days_to_day_number, event, today_count=0)


MAX_COUNT = 100
MAX_COEFF = 2.0
MIN_COEFF = 1.2


def _calculate_penalty(count: int) -> int:
    if count <= 0:
        return 0
    coeff = MIN_COEFF if count >= MAX_COUNT else MAX_COEFF - (count - 1) * (MAX_COEFF - MIN_COEFF) / (MAX_COUNT - 1)
    return round(count * coeff)
