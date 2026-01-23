import logging
from datetime import datetime, timedelta

from aiogram import Bot, F, Router, filters, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from punq import Container

from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.push_ups.application.interactors.create import CreatePushUpInteractor
from btc_challenge.push_ups.application.interactors.get_all_users_stats import GetAllUsersStatsInteractor
from btc_challenge.push_ups.application.interactors.get_all_users_stats_by_date import (
    GetAllUsersStatsByDateInteractor,
)
from btc_challenge.push_ups.application.interactors.get_daily_stats import GetDailyStatsInteractor
from btc_challenge.push_ups.presentation.states import PushUpStates
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.shared.presentation.checks import require_verified
from btc_challenge.shared.presentation.commands import Commands
from btc_challenge.users.adapters.sqlite.repository import UserRepository
from btc_challenge.users.domain.entity import User

push_ups_router = Router()
logger = logging.getLogger(__name__)


@push_ups_router.message(filters.Command(Commands.CANCEL))
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять")
        return

    await state.clear()
    await message.answer("Отменил")


@push_ups_router.message(filters.Command(Commands.ADD, Commands.PUSH_UP))
async def cmd_add_push_up(message: types.Message, state: FSMContext, user: User | None) -> None:
    if not await require_verified(message, user):
        return

    # Проверяем участие в активных событиях
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        now = datetime.now()
        active_events = await event_repository.get_active_events_by_participant(user.oid, now)

        if not active_events:
            await message.answer(
                f"❌ Ты не участвуешь ни в одном активном ивенте!\n\nИспользуй /{Commands.ACTIVE_EVENTS} чтобы посмотреть доступные ивенты.",
            )
            return

    await state.set_state(PushUpStates.waiting_for_count)
    await message.answer("Сколько отжиманий сделал?")


@push_ups_router.message(PushUpStates.waiting_for_count, F.text)
async def process_count(message: types.Message, state: FSMContext, user: User | None) -> None:
    if not await require_verified(message, user):
        await state.clear()
        return

    if not message.text:
        await message.answer("Введи количество отжиманий числом")
        return

    try:
        count = int(message.text)
        if count <= 0:
            await message.answer("Количество должно быть больше 0")
            return
    except ValueError:
        await message.answer("Введи корректное число")
        return

    await state.update_data(count=count)
    await state.set_state(PushUpStates.waiting_for_video)
    await message.answer(f"Отлично! Теперь отправь видео или кружок с {count} отжиманиями")


@push_ups_router.message(PushUpStates.waiting_for_count)
async def wrong_count_type(message: types.Message) -> None:
    await message.answer("Введи количество отжиманий числом")


@push_ups_router.message(PushUpStates.waiting_for_video, F.video | F.video_note)
async def process_video(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
    user: User | None,
) -> None:
    if not await require_verified(message, user):
        await state.clear()
        return

    if not message.from_user or not user:
        return

    user_id = message.from_user.id
    data = await state.get_data()
    count = data.get("count", 0)

    # Проверяем участие в активных событиях и ограничения
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        now = datetime.now()
        active_events = await event_repository.get_active_events_by_participant(user.oid, now)

        if active_events:
            # Берем первое активное событие для проверки ограничения
            event = active_events[0]
            day_number = event.day_number

            if count > day_number:
                await state.clear()
                await message.answer(
                    f"❌ Превышен лимит отжиманий!\n\n"
                    f"📌 Ивент: {event.title}\n"
                    f"📅 День {day_number} - максимум {day_number} отжиманий\n"
                    f"💪 Ты пытаешься загрузить: {count} отжиманий",
                )
                return

    # Определяем тип файла и получаем file_id
    file: types.Video | types.VideoNote | None = None
    is_video_note = False
    if message.video:
        file = message.video
        is_video_note = False
    elif message.video_note:
        file = message.video_note
        is_video_note = True
    else:
        return

    # Сохраняем в БД только file_id
    interactor = container.resolve(CreatePushUpInteractor)
    await interactor.execute(
        telegram_id=user_id,
        telegram_file_id=file.file_id,
        is_video_note=is_video_note,
        count=count,
    )

    await state.clear()
    await message.answer(f"Подход сохранен! {count} отжиманий 💪")

    # Отправляем уведомления участникам событий
    await _notify_event_participants(
        bot=bot,
        user=user,
        count=count,
        file_id=file.file_id,
        is_video_note=is_video_note,
    )


@push_ups_router.message(PushUpStates.waiting_for_video)
async def wrong_video_type(message: types.Message) -> None:
    await message.answer("Отправь видео или кружок с подтверждением")


@push_ups_router.message(filters.Command(Commands.INFO))
async def cmd_info(message: types.Message, container: Container, user: User | None) -> None:
    if not await require_verified(message, user):
        return

    if not message.from_user:
        return

    user_id = message.from_user.id

    interactor: GetDailyStatsInteractor = container.resolve(GetDailyStatsInteractor)
    try:
        stats = await interactor.execute(telegram_id=user_id)
    except ObjectNotFoundError:
        await message.answer(f"Сначала нажми /{Commands.START}")
        return

    if stats.push_ups_count == 0:
        await message.answer("Сегодня еще не было подходов")
        return

    # Отправляем статистику
    stats_text = f"📊 Статистика за сегодня:\n\nВсего отжиманий: {stats.total_count}\nПодходов: {stats.push_ups_count}"
    await message.answer(stats_text)

    # Отправляем видео
    for count, file_id, is_video_note in stats.videos:
        if is_video_note:
            await message.answer_video_note(video_note=file_id)
            await message.answer(f"Подход: {count} отжиманий")
        else:
            await message.answer_video(
                video=file_id,
                caption=f"Подход: {count} отжиманий",
            )


@push_ups_router.message(filters.Command(Commands.STATS, Commands.LEADERBOARD))
async def cmd_stats(message: types.Message, container: Container) -> None:
    interactor: GetAllUsersStatsInteractor = container.resolve(GetAllUsersStatsInteractor)
    stats_list = await interactor.execute()

    if not stats_list:
        await message.answer("Сегодня еще никто не отжимался")
        return

    # Формируем текст с рейтингом
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    stats_text = "🏆 Статистика за сегодня:\n\n"
    for idx, stats in enumerate(stats_list, start=1):
        medal = medals.get(idx, f"{idx}.")
        stats_text += f"{medal} @{stats.username}\nОтжиманий: {stats.total_count} ({stats.push_ups_count} подходов)\n\n"

    await message.answer(stats_text)


@push_ups_router.message(filters.Command(Commands.HISTORY))
async def cmd_history(message: types.Message, user: User | None) -> None:
    if not await require_verified(message, user):
        return

    # Создаем кнопки для выбора последних дней
    now = datetime.now()
    buttons = []
    for days_ago in range(7):
        target_date = now - timedelta(days=days_ago)
        label = "Сегодня" if days_ago == 0 else ("Вчера" if days_ago == 1 else target_date.strftime("%d.%m.%Y"))
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"history:{days_ago}")])

    buttons.append([InlineKeyboardButton(text="Другая дата", callback_data="history:custom")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выбери день для просмотра статистики:", reply_markup=keyboard)


@push_ups_router.callback_query(F.data.startswith("history:"))
async def process_history_callback(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
    user: User | None,
) -> None:
    if not callback.data or not callback.message:
        return

    if not await require_verified(callback.message, user):
        await callback.answer()
        return

    days_str = callback.data.split(":")[1]

    if days_str == "custom":
        await state.set_state(PushUpStates.waiting_for_date)
        await callback.message.answer("Введи дату в формате ДД.ММ.ГГГГ (например, 20.01.2026):")
        await callback.answer()
        return

    days_ago = int(days_str)
    target_date = datetime.now() - timedelta(days=days_ago)

    await _show_stats_for_date(callback.message, container, target_date)
    await callback.answer()


@push_ups_router.message(PushUpStates.waiting_for_date, F.text)
async def process_custom_date(
    message: types.Message,
    state: FSMContext,
    container: Container,
    user: User | None,
) -> None:
    if not await require_verified(message, user):
        await state.clear()
        return

    if not message.text:
        await message.answer("Введи дату в формате ДД.ММ.ГГГГ")
        return

    try:
        target_date = datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer(
            "Неверный формат даты. Используй формат ДД.ММ.ГГГГ (например, 20.01.2026)",
        )
        return

    await state.clear()
    await _show_stats_for_date(message, container, target_date)


@push_ups_router.message(PushUpStates.waiting_for_date)
async def wrong_date_type(message: types.Message) -> None:
    await message.answer("Введи дату текстом в формате ДД.ММ.ГГГГ")


async def _show_stats_for_date(
    message: types.Message,
    container: Container,
    target_date: datetime,
) -> None:
    """Show statistics for all users for a specific date."""
    interactor: GetAllUsersStatsByDateInteractor = container.resolve(GetAllUsersStatsByDateInteractor)
    stats_list = await interactor.execute(date=target_date)

    date_str = target_date.strftime("%d.%m.%Y")

    if not stats_list:
        await message.answer(f"📊 Статистика за {date_str}:\n\nВ этот день никто не отжимался")
        return

    # Формируем текст с рейтингом
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    stats_text = f"🏆 Статистика за {date_str}:\n\n"
    for idx, stats in enumerate(stats_list, start=1):
        medal = medals.get(idx, f"{idx}.")
        stats_text += f"{medal} @{stats.username}\nОтжиманий: {stats.total_count} ({stats.push_ups_count} подходов)\n\n"

    await message.answer(stats_text)

    # Отправляем видео каждого участника
    for stats in stats_list:
        if stats.videos:
            await message.answer(f"📹 Видео @{stats.username}:")
            for count, file_id, is_video_note in stats.videos:
                if is_video_note:
                    await message.answer_video_note(video_note=file_id)
                    await message.answer(f"@{stats.username}: {count} отжиманий")
                else:
                    await message.answer_video(
                        video=file_id,
                        caption=f"@{stats.username}: {count} отжиманий",
                    )


async def _notify_event_participants(
    bot: Bot,
    user: User,
    count: int,
    file_id: str,
    is_video_note: bool,
) -> None:
    """Send notification to event participants when user completes daily pushups."""
    try:
        async with get_async_session() as session:
            event_repository = EventRepository(session)
            user_repository = UserRepository(session)

            now = datetime.now()
            # Get active events where user is a participant
            active_events = await event_repository.get_active_events_by_participant(user.oid, now)

            for event in active_events:
                if not event.participant_oids:
                    continue

                # Calculate day number since event start
                day_number = (now.date() - event.start_at.date()).days + 1

                # Get all participants except the user who completed pushups
                other_participant_oids = [oid for oid in event.participant_oids if oid != user.oid]
                other_participant_oids = [oid for oid in event.participant_oids]
                if not other_participant_oids:
                    continue

                participants = await user_repository.get_many(oids=other_participant_oids)

                notification_text = (
                    f"🎉 @{user.username} выполнил дневную задачу!\n\n"
                    f"📌 Ивент: {event.title}\n"
                    f"📅 День {day_number}\n"
                    f"💪 Отжиманий: {count}"
                )

                # Send to all other participants
                for participant in participants:
                    logger.info(f"Sending notification to {participant.username} with id {participant.telegram_id}")
                    try:
                        if is_video_note:
                            await bot.send_video_note(
                                chat_id=participant.telegram_id,
                                video_note=file_id,
                            )
                            await bot.send_message(
                                chat_id=participant.telegram_id,
                                text=notification_text,
                            )
                        else:
                            await bot.send_video(
                                chat_id=participant.telegram_id,
                                video=file_id,
                                caption=notification_text,
                            )
                    except Exception:
                        # User might have blocked the bot
                        pass

    except Exception:
        # Don't fail the main flow if notifications fail
        pass
