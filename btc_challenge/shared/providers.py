import zoneinfo
from datetime import datetime


class TimeZone:
    MOSCOW = zoneinfo.ZoneInfo('Europe/Moscow')
    UTC = zoneinfo.ZoneInfo('UTC')


class DatetimeProvider:
    @classmethod
    def provide(cls, tz: zoneinfo.ZoneInfo = TimeZone.UTC) -> datetime:
        return datetime.now(tz=tz)
