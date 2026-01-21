from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class StoredObject:
    oid: UUID
    file_name: str
    storage_key: str
    size: int
    extension: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, file_name: str, storage_key: str, size: int, extension: str) -> "StoredObject":
        now = datetime.now()
        return cls(
            oid=uuid4(),
            file_name=file_name,
            storage_key=storage_key,
            size=size,
            extension=extension,
            created_at=now,
            updated_at=now,
        )
