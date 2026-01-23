from aiogram import Router, filters, types
from punq import Container

from btc_challenge.shared.errors import ObjectAlreadyExistsError
from btc_challenge.shared.presentation.commands import Commands
from btc_challenge.users.application.interactors.create import CreateUserInteractor

user_router = Router()


@user_router.message(filters.Command(Commands.START))
async def cmd_start(message: types.Message, container: Container) -> None:
    if not message.from_user:
        return
    user_id, username = message.from_user.id, message.from_user.username
    if not username:
        await message.answer(
            "❌ Для использования бота необходимо установить username в настройках Telegram.",
        )
        return

    interactor: CreateUserInteractor = container.resolve(CreateUserInteractor)
    is_new_user = False
    try:
        await interactor.execute(user_id=user_id, username=username)
        is_new_user = True
    except ObjectAlreadyExistsError:
        pass

    welcome_text = (
        "👋 Добро пожаловать в BTC Challenge!\n\n"
        "🔐 Для участия в ивентах необходимо пройти верификацию.\n"
        f"Используй команду /{Commands.CONFIRMATION} чтобы пройти верификацию.\n\n"
        "📋 Доступные команды:\n"
        f"/{Commands.CONFIRMATION} - Получить ссылку для верификации\n"
        f"/{Commands.ACTIVE_EVENTS} - Активные ивенты и участники\n"
        f"/{Commands.ADD} - Добавить отжимания (требуется участие в ивенте)\n"
        f"/{Commands.STATS} - Статистика за сегодня\n"
        f"/{Commands.HISTORY} - История по дням"
    )

    if is_new_user:
        await message.answer(f"{welcome_text}\n\n✅ Регистрация успешна!")
    else:
        await message.answer(welcome_text)
