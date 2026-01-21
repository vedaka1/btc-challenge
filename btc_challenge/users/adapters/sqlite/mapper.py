from btc_challenge.users.adapters.sqlite.model import UserORM
from btc_challenge.users.domain.entity import User


class SqliteUserMapper:
    @classmethod
    def to_entity(cls, user_orm: UserORM) -> User:
        return User(
            oid=user_orm.oid,
            telegram_id=user_orm.telegram_id,
            username=user_orm.username,
            created_at=user_orm.created_at,
            updated_at=user_orm.updated_at,
        )

    @classmethod
    def to_model(cls, user: User) -> UserORM:
        return UserORM(
            oid=user.oid,
            telegram_id=user.telegram_id,
            username=user.username,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
