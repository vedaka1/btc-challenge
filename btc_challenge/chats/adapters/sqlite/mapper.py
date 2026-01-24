from btc_challenge.chats.adapters.sqlite.model import ChatORM
from btc_challenge.chats.domain.entity import Chat


class SqliteChatMapper:
    @classmethod
    def to_entity(cls, chat_orm: ChatORM) -> Chat:
        return Chat(
            oid=chat_orm.oid,
            telegram_chat_id=chat_orm.telegram_chat_id,
            chat_type=chat_orm.chat_type,
            title=chat_orm.title,
            is_active=chat_orm.is_active,
            created_at=chat_orm.created_at,
            updated_at=chat_orm.updated_at,
        )

    @classmethod
    def to_model(cls, chat: Chat) -> ChatORM:
        return ChatORM(
            oid=chat.oid,
            telegram_chat_id=chat.telegram_chat_id,
            chat_type=chat.chat_type,
            title=chat.title,
            is_active=chat.is_active,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )
