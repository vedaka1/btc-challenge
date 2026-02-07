from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.mixins import DatetimeMixin, IdentityMixin
from btc_challenge.shared.adapters.sqlite.models import BaseORM


class ChatORM(BaseORM, IdentityMixin, DatetimeMixin):
    __tablename__ = 'chats'

    telegram_chat_id: Mapped[int] = mapped_column(unique=True)
    chat_type: Mapped[str]
    title: Mapped[str | None]
    is_active: Mapped[bool]
