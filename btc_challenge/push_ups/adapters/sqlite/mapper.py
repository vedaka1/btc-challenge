from btc_challenge.push_ups.adapters.sqlite.model import PushUpORM
from btc_challenge.push_ups.domain.entity import PushUp


class SqlitePushUpMapper:
    @classmethod
    def to_entity(cls, push_up_orm: PushUpORM) -> PushUp:
        return PushUp(
            oid=push_up_orm.oid,
            user_oid=push_up_orm.user_oid,
            telegram_file_id=push_up_orm.telegram_file_id,
            is_video_note=push_up_orm.is_video_note,
            count=push_up_orm.count,
            created_at=push_up_orm.created_at,
            updated_at=push_up_orm.updated_at,
        )

    @classmethod
    def to_model(cls, push_up: PushUp) -> PushUpORM:
        return PushUpORM(
            oid=push_up.oid,
            user_oid=push_up.user_oid,
            telegram_file_id=push_up.telegram_file_id,
            is_video_note=push_up.is_video_note,
            count=push_up.count,
            created_at=push_up.created_at,
            updated_at=push_up.updated_at,
        )
