from btc_challenge.chats.domain.repository import IChatRepository
from btc_challenge.shared.application.commiter import ICommiter


class DeactivateChatInteractor:
    def __init__(self, chat_repository: IChatRepository, commiter: ICommiter):
        self._chat_repository = chat_repository
        self._commiter = commiter

    async def execute(self, telegram_chat_id: int) -> None:
        chat = await self._chat_repository.get_by_telegram_chat_id(telegram_chat_id)
        if not chat:
            return

        chat.deactivate()
        await self._chat_repository.update(chat)
        await self._commiter.commit()
