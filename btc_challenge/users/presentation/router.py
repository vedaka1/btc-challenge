from aiogram import Router, filters, types
from punq import Container

from btc_challenge.shared.errors import ObjectAlreadyExistsError
from btc_challenge.users.application.interactors.create import CreateUserInteractor

user_router = Router()


@user_router.message(filters.Command("start"))
async def cmd_start(message: types.Message, container: Container) -> None:
    if not message.from_user:
        return
    user_id, username = message.from_user.id, message.from_user.username
    if not username:
        return

    interactor: CreateUserInteractor = container.resolve(CreateUserInteractor)
    try:
        await interactor.execute(user_id=user_id, username=username)
    except ObjectAlreadyExistsError:
        pass
