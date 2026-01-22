from aiogram import Bot, F, Router, filters, types
from punq import Container

from btc_challenge.config import AppConfig
from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.users.application.interactors.verify import VerifyUserInteractor
from btc_challenge.users.domain.repository import IUserRepository

verification_router = Router()


@verification_router.message(filters.Command("confirmation"))
async def cmd_confirmation(message: types.Message, bot: Bot, container: Container) -> None:
    if not message.from_user:
        return

    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    # Get user from repository to check if exists
    user_repository: IUserRepository = container.resolve(IUserRepository)
    user = await user_repository.get_by_telegram_id(user_id)

    if not user:
        await message.answer("Сначала нажми /start")
        return
    if user.is_verified:
        await message.answer("Ты уже верифицирован!")
        return

    # Create inline keyboard with approve/reject buttons
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"verify_approve_{user_id}",
                ),
                types.InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"verify_reject_{user_id}",
                ),
            ],
        ],
    )

    # Send verification request to all admins
    admin_message = (
        f"🔔 Запрос на верификацию\n\nUser ID: {user_id}\nUsername: @{username}\nИмя: {message.from_user.full_name}"
    )
    for admin_id in AppConfig.telegram.admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=keyboard,
            )
        except Exception:
            # Admin might have blocked the bot or chat doesn't exist
            pass

    await message.answer("Запрос на верификацию отправлен администраторам. Ожидай подтверждения.")


@verification_router.callback_query(F.data.startswith("verify_"))
async def process_verification(callback: types.CallbackQuery, bot: Bot, container: Container) -> None:
    if not callback.data or not callback.from_user or not callback.message:
        return

    # Check if the callback is from an admin
    if callback.from_user.id not in AppConfig.telegram.admin_ids:
        await callback.answer("У тебя нет прав для выполнения этого действия", show_alert=True)
        return

    parts = callback.data.split("_")
    user_id = int(parts[2])
    is_verified = parts[1] == "approve"

    # Update user verification status
    interactor: VerifyUserInteractor = container.resolve(VerifyUserInteractor)
    try:
        await interactor.execute(telegram_id=user_id, is_verified=is_verified)
    except ObjectNotFoundError:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    status_text = "✅ ПОДТВЕРЖДЕН" if is_verified else "❌ ОТКЛОНЕН"
    updated_text = f"{callback.message.text}\n\n{status_text} администратором @{callback.from_user.username}"
    await callback.message.edit_text(text=updated_text)
    await callback.answer(f"Пользователь {status_text.lower()}")

    result_message = (
        "✅ Твоя заявка на верификацию подтверждена!" if is_verified else "❌ Твоя заявка на верификацию отклонена."
    )

    try:
        await bot.send_message(chat_id=user_id, text=result_message)
    except Exception:
        # User might have blocked the bot
        pass
