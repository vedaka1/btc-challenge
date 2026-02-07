from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.mixins import DatetimeMixin, IdentityMixin
from btc_challenge.shared.adapters.sqlite.models import BaseORM


class UserORM(BaseORM, IdentityMixin, DatetimeMixin):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    is_verified: Mapped[bool]
