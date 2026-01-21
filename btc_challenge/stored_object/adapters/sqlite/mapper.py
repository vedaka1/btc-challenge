from btc_challenge.stored_object.adapters.sqlite.model import StoredObjectORM
from btc_challenge.stored_object.domain.entity import StoredObject


class SqliteStoredObjectMapper:
    @classmethod
    def to_entity(cls, stored_object_orm: StoredObjectORM) -> StoredObject:
        return StoredObject(
            oid=stored_object_orm.oid,
            file_name=stored_object_orm.file_name,
            storage_key=stored_object_orm.storage_key,
            size=stored_object_orm.size,
            extension=stored_object_orm.extension,
            created_at=stored_object_orm.created_at,
            updated_at=stored_object_orm.updated_at,
        )

    @classmethod
    def to_model(cls, stored_object: StoredObject) -> StoredObjectORM:
        return StoredObjectORM(
            oid=stored_object.oid,
            file_name=stored_object.file_name,
            storage_key=stored_object.storage_key,
            size=stored_object.size,
            extension=stored_object.extension,
            created_at=stored_object.created_at,
            updated_at=stored_object.updated_at,
        )
