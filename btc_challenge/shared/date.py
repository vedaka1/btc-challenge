from datetime import UTC, datetime
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def to_moscow(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC).astimezone(MOSCOW_TZ).replace(tzinfo=None)


def from_moscow(dt: datetime) -> datetime:
    return dt.replace(tzinfo=MOSCOW_TZ).astimezone(UTC).replace(tzinfo=None)


def get_current_day_range() -> tuple[datetime, datetime]:
    now = datetime.now()
    begin_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return begin_date, end_date
