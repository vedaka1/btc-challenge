from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from btc_challenge.shared.providers import DatetimeProvider

MOSCOW_TZ = ZoneInfo('Europe/Moscow')


def to_moscow(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC).astimezone(MOSCOW_TZ).replace(tzinfo=None)


def from_moscow(dt: datetime) -> datetime:
    return dt.replace(tzinfo=MOSCOW_TZ).astimezone(UTC).replace(tzinfo=None)


def get_moscow_day_range(dt: datetime | None = None) -> tuple[datetime, datetime]:
    """Возвращает начало и конец дня по московскому времени в UTC."""
    if dt is None:
        dt = DatetimeProvider.provide()
    now_moscow = dt.astimezone(MOSCOW_TZ)
    begin_moscow = now_moscow.replace(hour=0, minute=0, second=0, microsecond=0)
    end_moscow = now_moscow.replace(hour=23, minute=59, second=59, microsecond=999999)
    return begin_moscow.astimezone(UTC), end_moscow.astimezone(UTC)
