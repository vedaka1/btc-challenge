from datetime import UTC, datetime, timezone


class DatetimeProvider:
    @classmethod
    def provide(cls, tz: timezone = UTC) -> datetime:
        return datetime.now(tz=tz)
