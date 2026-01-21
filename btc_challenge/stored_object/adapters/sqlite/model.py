from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column

from btc_challenge.shared.adapters.sqlite.models import BaseORM


class StoredObjectORM(BaseORM):
    __tablename__ = "stored_object"

    oid: Mapped[UUID] = mapped_column(primary_key=True)
    file_name: Mapped[str]
    storage_key: Mapped[str]
    size: Mapped[int]
    extension: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
