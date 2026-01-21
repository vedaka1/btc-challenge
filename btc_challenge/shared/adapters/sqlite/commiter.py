from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from btc_challenge.shared.application.commiter import ICommiter
from btc_challenge.shared.errors import ObjectAlreadyExistsError


class Commiter(ICommiter):
    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise ObjectAlreadyExistsError from None

    async def rollback(self) -> None:
        await self._session.rollback()

    async def close(self) -> None:
        await self._session.close()
