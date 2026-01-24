from datetime import UTC, datetime
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def to_moscow(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC).astimezone(MOSCOW_TZ).replace(tzinfo=None)


def from_moscow(dt: datetime) -> datetime:
    return dt.replace(tzinfo=MOSCOW_TZ).astimezone(UTC).replace(tzinfo=None)
