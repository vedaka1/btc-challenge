from btc_challenge.events.domain.entity import Event


def pluralize_pushups(count: int) -> str:
    """Return correctly pluralized form of 'pushup' in Russian.

    Examples:
        1 отжимание
        2 отжимания
        5 отжиманий
        21 отжимание
        22 отжимания
        25 отжиманий
    """
    if 11 <= count % 100 <= 19:
        return "отжиманий"
    last_digit = count % 10
    if last_digit == 1:
        return "отжимание"
    if 2 <= last_digit <= 4:
        return "отжимания"
    return "отжиманий"


def create_event_notification_text(event: Event) -> str:
    """Create notification text for event daily reminder."""
    pushups_word = pluralize_pushups(event.day_number)
    return f"{event.str_info}\n\nСегодня нужно сделать {event.day_number} {pushups_word}!"
