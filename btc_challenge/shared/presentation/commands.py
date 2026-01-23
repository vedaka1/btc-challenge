from enum import StrEnum


class Commands(StrEnum):
    START = "start"
    ADD = "add"
    PUSH_UP = "push_up"
    INFO = "info"
    STATS = "stats"
    LEADERBOARD = "leaderboard"
    HISTORY = "history"
    CANCEL = "cancel"
    ACTIVE_EVENTS = "active_events"
    CONFIRMATION = "confirmation"
    CREATE_EVENT = "create_event"
