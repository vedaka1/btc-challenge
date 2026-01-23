from datetime import datetime, timedelta

from aiogram import Bot, F, Router, filters, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from punq import Container

from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.events.application.interactors.create import CreateEventInteractor
from btc_challenge.events.application.interactors.get_participants import GetEventParticipantsInteractor
from btc_challenge.events.application.interactors.join import JoinEventInteractor
from btc_challenge.events.domain.entity import Event
from btc_challenge.events.presentation.states import CreateEventStates
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.shared.presentation.checks import require_admin, require_verified
from btc_challenge.shared.presentation.commands import Commands
from btc_challenge.users.adapters.sqlite.repository import UserRepository
from btc_challenge.users.domain.entity import User

events_router = Router()


@events_router.message(filters.Command(Commands.CREATE_EVENT))
async def cmd_create_event(message: types.Message, state: FSMContext, user: User | None) -> None:
    if not await require_admin(message, user):
        return

    await state.set_state(CreateEventStates.waiting_for_title)
    await message.answer("Введите название ивента:")


@events_router.message(CreateEventStates.waiting_for_title, F.text)
async def process_title(message: types.Message, state: FSMContext, user: User | None) -> None:
    if not await require_admin(message, user):
        await state.clear()
        return

    if not message.text:
        await message.answer("Введите название ивента:")
        return

    await state.update_data(title=message.text)
    await state.set_state(CreateEventStates.waiting_for_description)
    await message.answer("Введите описание ивента:")


@events_router.message(CreateEventStates.waiting_for_title)
async def wrong_title_type(message: types.Message) -> None:
    await message.answer("Введите название текстом")


@events_router.message(CreateEventStates.waiting_for_description, F.text)
async def process_description(message: types.Message, state: FSMContext, user: User | None) -> None:
    if not await require_admin(message, user):
        await state.clear()
        return

    if not message.text:
        await message.answer("Введите описание ивента:")
        return

    await state.update_data(description=message.text)
    await state.set_state(CreateEventStates.waiting_for_start_at)
    example_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    await message.answer(f"Введите дату и время начала в формате:\nДД.ММ.ГГГГ ЧЧ:ММ\nНапример: {example_date}")


@events_router.message(CreateEventStates.waiting_for_description)
async def wrong_description_type(message: types.Message) -> None:
    await message.answer("Введите описание текстом")


@events_router.message(CreateEventStates.waiting_for_start_at, F.text)
async def process_start_at(message: types.Message, state: FSMContext, user: User | None) -> None:
    if not await require_admin(message, user):
        await state.clear()
        return

    if not message.text:
        await message.answer("Введите дату и время начала:")
        return

    try:
        start_at = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    except ValueError:
        example_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        await message.answer(f"Неверный формат даты. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\nНапример: {example_date}")
        return

    # Check if date is in the future
    if start_at <= datetime.now():
        await message.answer("Дата начала должна быть в будущем")
        return

    await state.update_data(start_at=start_at)
    await state.set_state(CreateEventStates.waiting_for_end_at)
    example_date = (start_at + timedelta(hours=1)).strftime("%d.%m.%Y %H:%M")
    await message.answer(f"Введите дату и время окончания в формате:\nДД.ММ.ГГГГ ЧЧ:ММ\nНапример: {example_date}")


@events_router.message(CreateEventStates.waiting_for_start_at)
async def wrong_start_at_type(message: types.Message) -> None:
    await message.answer("Введите дату и время начала в формате: ДД.ММ.ГГГГ ЧЧ:ММ")


@events_router.message(CreateEventStates.waiting_for_end_at, F.text)
async def process_end_at(
    message: types.Message,
    state: FSMContext,
    container: Container,
    bot: Bot,
    user: User | None,
) -> None:
    if not await require_admin(message, user):
        await state.clear()
        return

    # After require_admin check, user is guaranteed to exist
    if not user:
        await state.clear()
        return

    if not message.text:
        await message.answer("Введите дату и время окончания:")
        return

    data = await state.get_data()
    start_at = data["start_at"]
    try:
        end_at = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    except ValueError:
        example_date = (start_at + timedelta(hours=1)).strftime("%d.%m.%Y %H:%M")
        await message.answer(
            f"Неверный формат даты. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\nНапример: {example_date}",
        )
        return

    if end_at <= start_at:
        await message.answer("Дата окончания должна быть позже даты начала")
        return

    # Create event
    interactor: CreateEventInteractor = container.resolve(CreateEventInteractor)
    try:
        event = await interactor.execute(
            creator_oid=user.oid,
            title=data["title"],
            description=data["description"],
            start_at=start_at,
            end_at=end_at,
        )
    except ValueError as e:
        await message.answer(f"Ошибка создания ивента: {e}")
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"✅ Ивент создан!\n\n"
        f"📌 {event.title}\n"
        f"📝 {event.description}\n"
        f"🕐 Начало: {event.start_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"🕐 Конец: {event.end_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Отправляю приглашения пользователям...",
    )

    # Send invitations to all verified users
    await send_event_invitations(bot, event)


@events_router.message(CreateEventStates.waiting_for_end_at)
async def wrong_end_at_type(message: types.Message) -> None:
    await message.answer("Введите дату и время окончания в формате: ДД.ММ.ГГГГ ЧЧ:ММ")


@events_router.callback_query(F.data.startswith("join_event:"))
async def handle_join_event(
    callback: types.CallbackQuery,
    container: Container,
    user: User | None,
) -> None:
    from uuid import UUID

    if not user:
        await callback.answer(f"Сначала нажми /{Commands.START}", show_alert=True)
        return

    if not user.is_verified:
        await callback.answer(
            f"Ты не верифицирован! Отправь команду /{Commands.CONFIRMATION} для верификации.",
            show_alert=True,
        )
        return

    event_oid = UUID(callback.data.split(":")[1])

    interactor: JoinEventInteractor = container.resolve(JoinEventInteractor)
    try:
        await interactor.execute(event_oid=event_oid, user_oid=user.oid)
        await callback.answer("Вы записаны на ивент!")
        # Update message to show confirmation
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer("✅ Вы записаны на ивент!")
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)


@events_router.message(filters.Command(Commands.ACTIVE_EVENTS))
async def cmd_active_events(message: types.Message, container: Container, user: User | None) -> None:
    if not await require_verified(message, user):
        return

    async with get_async_session() as session:
        event_repository = EventRepository(session)
        now = datetime.now()
        active_events = await event_repository.get_active_events(now)

        if not active_events:
            await message.answer("📭 Сейчас нет активных ивентов")
            return

        # Show each active event with participants
        interactor: GetEventParticipantsInteractor = container.resolve(GetEventParticipantsInteractor)

        for event in active_events:
            participants = await interactor.execute(event_oid=event.oid)
            day_number = (now.date() - event.start_at.date()).days + 1

            participants_text = (
                "\n".join([f"  • @{p.username}" for p in participants]) if participants else "  Нет участников"
            )

            event_text = (
                f"🎯 {event.title}\n\n"
                f"📝 {event.description}\n\n"
                f"📅 День {day_number}\n"
                f"🕐 Начало: {event.start_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"🕐 Конец: {event.end_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"👥 Участники ({len(participants)}):\n{participants_text}"
            )

            await message.answer(event_text)


async def send_event_invitations(bot: Bot, event: "Event") -> None:
    """Send event invitation to all verified users."""
    async with get_async_session() as session:
        user_repository = UserRepository(session)
        users = await user_repository.get_many()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Участвую", callback_data=f"join_event:{event.oid}")],
            ],
        )

        invitation_text = (
            f"🎉 Новый ивент!\n\n"
            f"📌 {event.title}\n"
            f"📝 {event.description}\n"
            f"🕐 Начало: {event.start_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"🕐 Конец: {event.end_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Хочешь принять участие? Нажми кнопку ниже!"
        )

        for user in users:
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=invitation_text,
                    reply_markup=keyboard,
                )
            except Exception:
                # User might have blocked the bot
                pass

        # Mark initial notification as sent
        async with get_async_session() as db_session:
            event_repository = EventRepository(db_session)
            event.initial_notification_sent = True
            await event_repository.save(event)
            await db_session.commit()
