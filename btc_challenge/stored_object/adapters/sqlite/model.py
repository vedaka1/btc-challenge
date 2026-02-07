from sqlalchemy.orm import Mapped

from btc_challenge.shared.adapters.sqlite.mixins import DatetimeMixin, IdentityMixin
from btc_challenge.shared.adapters.sqlite.models import BaseORM


class StoredObjectORM(BaseORM, IdentityMixin, DatetimeMixin):
    __tablename__ = 'stored_object'

    file_name: Mapped[str]
    storage_key: Mapped[str]
    size: Mapped[int]
    extension: Mapped[str]
