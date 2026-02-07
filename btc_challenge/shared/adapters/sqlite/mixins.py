from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column


class IdentityMixin(MappedAsDataclass):
    oid: Mapped[UUID] = mapped_column(primary_key=True)
    'Идентификатор'


class DatetimeMixin(MappedAsDataclass):
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    'Время создания'
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    'Время обновления'
