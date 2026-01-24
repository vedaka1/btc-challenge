import logging
from datetime import datetime
from uuid import UUID

from aiogram import Bot, F, Router, filters, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from punq import Container

from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.events.application.interactors.complete import CompleteEventInteractor
from btc_challenge.events.application.interactors.create import CreateEventInteractor
from btc_challenge.events.application.interactors.get_participants import GetEventParticipantsInteractor
from btc_challenge.events.application.interactors.join import JoinEventInteractor
from btc_challenge.events.domain.entity import Event
from btc_challenge.events.presentation.states import CreateEventStates
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.shared.presentation.checks import require_admin, require_verified
from btc_challenge.shared.presentation.commands import Commands
from btc_challenge.shared.tasks.send_to_groups import send_notification_to_groups
from btc_challenge.users.adapters.sqlite.repository import UserRepository
from btc_challenge.users.domain.entity import User

events_router = Router()
logger = logging.getLogger(__name__)


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
async def process_start_at(
    message: types.Message,
    state: FSMContext,
    container: Container,
    bot: Bot,
    user: User | None,
) -> None:
    logger.info(f"process_start_at: received message from user {message.from_user.id}")

    if not await require_admin(message, user):
        logger.warning(f"process_start_at: user {message.from_user.id} is not admin")
        await state.clear()
        return

    # After require_admin check, user is guaranteed to exist
    if not user:
        logger.error("process_start_at: user is None after require_admin check")
        await state.clear()
        return

    if not message.text:
        await message.answer("Введите дату и время начала:")
        return

    logger.info(f"process_start_at: parsing date '{message.text}'")

    try:
        start_at = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        logger.info(f"process_start_at: parsed date: {start_at}")
    except ValueError as e:
        logger.error(f"process_start_at: failed to parse date: {e}")
        example_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        await message.answer(f"Неверный формат даты. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\nНапример: {example_date}")
        return

    data = await state.get_data()
    logger.info(f"process_start_at: state data: {data}")

    # Check if we have required data
    if "title" not in data or "description" not in data:
        logger.error("process_start_at: missing title or description in state data")
        await message.answer("Ошибка: данные ивента не найдены. Начните заново с /create_event")
        await state.clear()
        return

    # Create event
    logger.info("process_start_at: creating event")
    interactor: CreateEventInteractor = container.resolve(CreateEventInteractor)
    try:
        event = await interactor.execute(
            creator_oid=user.oid,
            title=data["title"],
            description=data["description"],
            start_at=start_at,
        )
        logger.info(f"process_start_at: event created successfully: {event.oid}")
    except ValueError as e:
        logger.error(f"process_start_at: failed to create event: {e}")
        await message.answer(f"Ошибка создания ивента: {e}")
        await state.clear()
        return

    await state.clear()
    await message.answer(
        f"✅ Ивент создан!\n\n"
        f"📌 {event.title}\n"
        f"📝 {event.description}\n"
        f"🕐 Начало: {event.start_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Отправляю приглашения пользователям...",
    )

    # Send invitations to all verified users
    await send_event_invitations(bot, event)


@events_router.message(CreateEventStates.waiting_for_start_at)
async def wrong_start_at_type(message: types.Message) -> None:
    await message.answer("Введите дату и время начала в формате: ДД.ММ.ГГГГ ЧЧ:ММ")


@events_router.callback_query(F.data.startswith("join_event:"))
async def handle_join_event(
    callback: types.CallbackQuery,
    container: Container,
    user: User | None,
) -> None:
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
        await callback.answer("✅ Вы записаны на ивент!", show_alert=True)

        # In private chat, remove button and send confirmation
        # In group chat, keep button for other users
        if callback.message and callback.message.chat.type == "private":
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
                f"🕐 Начало: {event.start_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"👥 Участники ({len(participants)}):\n{participants_text}"
            )

            await message.answer(event_text)


@events_router.message(filters.Command(Commands.COMPLETE_EVENT))
async def cmd_complete_event(message: types.Message, container: Container, user: User | None) -> None:
    if not await require_admin(message, user):
        return

    # Get current active event
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        active_event = await event_repository.get_current_active_event()

        if not active_event:
            await message.answer("📭 Нет активного ивента для завершения")
            return

        # Show event info and ask for confirmation
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да, завершить", callback_data=f"complete_event:{active_event.oid}"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="complete_event:cancel"),
                ],
            ],
        )

        day_number = (datetime.now().date() - active_event.start_at.date()).days + 1

        confirmation_text = (
            f"⚠️ Вы уверены, что хотите завершить ивент?\n\n"
            f"📌 {active_event.title}\n"
            f"📝 {active_event.description}\n"
            f"📅 День {day_number}\n"
            f"👥 Участников: {len(active_event.participant_oids)}"
        )

        await message.answer(confirmation_text, reply_markup=keyboard)


@events_router.callback_query(F.data.startswith("complete_event:"))
async def handle_complete_event(
    callback: types.CallbackQuery,
    container: Container,
    user: User | None,
) -> None:
    if not user:
        await callback.answer(f"Сначала нажми /{Commands.START}", show_alert=True)
        return

    # Check admin
    if not await require_admin(callback.message, user):
        await callback.answer("Только администраторы могут завершать ивенты", show_alert=True)
        return

    action = callback.data.split(":")[1]

    if action == "cancel":
        await callback.message.edit_text("❌ Завершение ивента отменено")
        return

    event_oid = UUID(action)

    # Complete the event

    interactor: CompleteEventInteractor = container.resolve(CompleteEventInteractor)
    try:
        event = await interactor.execute(event_oid=event_oid)

        # Get participants stats

        participants_interactor: GetEventParticipantsInteractor = container.resolve(GetEventParticipantsInteractor)
        participants = await participants_interactor.execute(event_oid=event.oid)

        participants_text = (
            "\n".join([f"  • @{p.username}" for p in participants]) if participants else "  Нет участников"
        )

        day_number = (datetime.now().date() - event.start_at.date()).days + 1

        await callback.message.edit_text(
            f"✅ Ивент завершен!\n\n"
            f"📌 {event.title}\n"
            f"📅 Продолжительность: {day_number} дней\n"
            f"👥 Участников: {len(participants)}\n\n"
            f"Список участников:\n{participants_text}",
        )

        await callback.answer("Ивент успешно завершен!")
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)


async def send_event_invitations(bot: Bot, event: "Event") -> None:
    """Send event invitation to all verified users and active chats."""
    async with get_async_session() as session:
        user_repository = UserRepository(session)

        # Send to verified users
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
            f"🕐 Начало: {event.start_at.strftime('%d.%m.%Y %H:%M')}\n\n"
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

        # Send to active chats (groups)
        await send_notification_to_groups(bot, session, invitation_text, keyboard)

        await session.commit()
