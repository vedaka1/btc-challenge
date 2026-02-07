import logging
from datetime import datetime, timedelta

from aiogram import Bot, F, Router, filters, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from punq import Container

from btc_challenge.chats.adapters.sqlite.repository import ChatRepository
from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.push_ups.adapters.sqlite.repository import PushUpRepository
from btc_challenge.push_ups.application.interactors.create import CreatePushUpInteractor
from btc_challenge.push_ups.application.interactors.get_all_users_stats import GetAllUsersStatsInteractor
from btc_challenge.push_ups.application.interactors.get_all_users_stats_by_date import (
    GetAllUsersStatsByDateInteractor,
)
from btc_challenge.push_ups.application.interactors.get_daily_stats import GetDailyStatsInteractor
from btc_challenge.push_ups.presentation.states import PushUpStates
from btc_challenge.shared.adapters.sqlite.session import get_async_session
from btc_challenge.shared.date import get_moscow_day_range
from btc_challenge.shared.errors import ObjectNotFoundError
from btc_challenge.shared.presentation.checks import require_verified
from btc_challenge.shared.presentation.commands import Commands
from btc_challenge.shared.providers import DatetimeProvider
from btc_challenge.shared.utils import pluralize_pushups
from btc_challenge.users.adapters.sqlite.repository import UserRepository
from btc_challenge.users.domain.entity import User

push_ups_router = Router()
logger = logging.getLogger(__name__)


@push_ups_router.message(filters.Command(Commands.CANCEL))
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer('Нечего отменять')
        return

    await state.clear()
    await message.answer('Отменил')


@push_ups_router.message(filters.Command(Commands.ADD, Commands.PUSH_UP))
async def cmd_add_push_up(message: types.Message, state: FSMContext, user: User | None) -> None:
    if not await require_verified(message, user):
        return

    # Запрещаем создание отжиманий в группах
    if message.chat.type in ('group', 'supergroup'):
        await message.answer('❌ Добавление отжиманий доступно только в личных сообщениях с ботом')
        return

    # Проверяем участие в активных событиях
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        push_up_repository = PushUpRepository(session)
        now = DatetimeProvider.provide()
        active_events = await event_repository.get_active_events_by_participant(user.oid, now)

        if not active_events:
            await message.answer(
                f'❌ Ты не участвуешь ни в одном активном ивенте!\n\n'
                f'Используй /{Commands.ACTIVE_EVENTS} чтобы посмотреть доступные ивенты.',
            )
            return

        # Используем day_number из активного события
        event = active_events[0]
        count = event.day_number

        begin_date, end_date = get_moscow_day_range()
        push_ups = await push_up_repository.get_by_user_oid_and_date(
            user_oid=user.oid,
            begin_date=begin_date,
            end_date=end_date,
        )
        if push_ups:
            await message.answer('❌ Ты уже отжимался сегодня')
            return

    await state.update_data(count=count)
    await state.set_state(PushUpStates.waiting_for_video)
    await message.answer(f'Отправь видео или кружок с отжиманиями: {count}')


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
    count = data.get('count', 0)

    if count <= 0:
        await message.answer('Ошибка: некорректное количество отжиманий')
        await state.clear()
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
    interactor: CreatePushUpInteractor = container.resolve(CreatePushUpInteractor)
    await interactor.execute(
        telegram_id=user_id,
        telegram_file_id=file.file_id,
        is_video_note=is_video_note,
        count=count,
    )

    await state.clear()
    await message.answer(f'Подход сохранен! {count} {pluralize_pushups(count)} 💪')

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
    await message.answer('Отправь видео или кружок с подтверждением')


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
        await message.answer(f'Сначала нажми /{Commands.START}')
        return

    if stats.push_ups_count == 0:
        await message.answer('Сегодня еще не было подходов')
        return

    # Получаем статистику за ивент
    event_total = 0
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        active_event = await event_repository.get_current_active_event()

        if active_event:
            push_up_repository = PushUpRepository(session)
            now = DatetimeProvider.provide()
            event_begin = active_event.start_at.replace(hour=0, minute=0, second=0, microsecond=0)
            event_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

            event_pushups = await push_up_repository.get_by_user_oid_and_date(
                user_oid=user.oid,
                begin_date=event_begin,
                end_date=event_end,
            )
            event_total = sum(p.count for p in event_pushups)

    # Отправляем статистику
    stats_text = f'📊 Статистика за сегодня:\n\nВсего отжиманий: {stats.total_count}\nПодходов: {stats.push_ups_count}'
    if active_event and event_total > 0:
        stats_text += f'\n\n🔥 За время ивента: {event_total}'
    await message.answer(stats_text)

    # Отправляем видео
    for count, file_id, is_video_note in stats.videos:
        if is_video_note:
            await message.answer_video_note(video_note=file_id)
            await message.answer(f'Подход: {count} {pluralize_pushups(count)}')
        else:
            await message.answer_video(
                video=file_id,
                caption=f'Подход: {count} {pluralize_pushups(count)}',
            )


@push_ups_router.message(filters.Command(Commands.STATS, Commands.LEADERBOARD))
async def cmd_stats(message: types.Message, container: Container) -> None:
    # Получаем начало и конец сегодняшнего дня по Москве
    begin_date, end_date = get_moscow_day_range()
    interactor: GetAllUsersStatsInteractor = container.resolve(GetAllUsersStatsInteractor)
    stats_list = await interactor.execute(begin_date, end_date)

    if not stats_list:
        await message.answer('Сегодня еще никто не отжимался')
        return

    # Получаем статистику за ивент
    event_stats = {}
    total_event_pushups = 0
    async with get_async_session() as session:
        event_repository = EventRepository(session)
        active_event = await event_repository.get_current_active_event()

        if active_event:
            push_up_repository = PushUpRepository(session)
            now = DatetimeProvider.provide()
            event_begin = active_event.start_at.replace(hour=0, minute=0, second=0, microsecond=0)
            event_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

            user_repository = UserRepository(session)
            all_users = await user_repository.get_many(is_verified=True)
            user_oids = [user.oid for user in all_users]

            all_event_pushups = await push_up_repository.get_by_user_oids_and_date(
                user_oids=user_oids,
                begin_date=event_begin,
                end_date=event_end,
            )

            # Группируем по пользователям
            user_map = {user.oid: user for user in all_users}
            for push_up in all_event_pushups:
                user = user_map.get(push_up.user_oid)
                if user:
                    if user.username not in event_stats:
                        event_stats[user.username] = 0
                    event_stats[user.username] += push_up.count
                    total_event_pushups += push_up.count

    # Формируем текст с рейтингом
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    stats_text = '🏆 Статистика за сегодня:\n\n'
    if active_event:
        total_today = sum(stats.total_count for stats in stats_list)
        stats_text += f'💪 Всего за день: {total_today}\n'
        stats_text += f'🔥 Всего за ивент: {total_event_pushups}\n\n'

    for idx, stats in enumerate(stats_list, start=1):
        medal = medals.get(idx, f'{idx}.')
        event_info = ''
        if active_event and stats.username in event_stats:
            event_info = f' (за ивент: {event_stats[stats.username]})'
        stats_text += f'{medal} @{stats.username}\nОтжиманий: {stats.total_count} ({stats.push_ups_count} подходов){event_info}\n\n'

    await message.answer(stats_text)


@push_ups_router.message(filters.Command(Commands.HISTORY))
async def cmd_history(message: types.Message, user: User | None) -> None:
    if not await require_verified(message, user):
        return

    # Создаем кнопки для выбора последних дней
    now = DatetimeProvider.provide()
    buttons = []
    for days_ago in range(7):
        target_date = now - timedelta(days=days_ago)
        label = 'Сегодня' if days_ago == 0 else ('Вчера' if days_ago == 1 else target_date.strftime('%d.%m.%Y'))
        buttons.append([InlineKeyboardButton(text=label, callback_data=f'history:{days_ago}')])

    buttons.append([InlineKeyboardButton(text='Другая дата', callback_data='history:custom')])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer('Выбери день для просмотра статистики:', reply_markup=keyboard)


@push_ups_router.callback_query(F.data.startswith('history:'))
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

    days_str = callback.data.split(':')[1]

    if days_str == 'custom':
        await state.set_state(PushUpStates.waiting_for_date)
        await callback.message.answer('Введи дату в формате ДД.ММ.ГГГГ (например, 20.01.2026):')
        await callback.answer()
        return

    try:
        days_ago = int(days_str)
    except ValueError:
        await callback.answer('Некорректные данные', show_alert=True)
        return

    target_date = DatetimeProvider.provide() - timedelta(days=days_ago)

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
        await message.answer('Введи дату в формате ДД.ММ.ГГГГ')
        return

    try:
        target_date = datetime.strptime(message.text, '%d.%m.%Y')
    except ValueError:
        await message.answer(
            'Неверный формат даты. Используй формат ДД.ММ.ГГГГ (например, 20.01.2026)',
        )
        return

    await state.clear()
    await _show_stats_for_date(message, container, target_date)


@push_ups_router.message(PushUpStates.waiting_for_date)
async def wrong_date_type(message: types.Message) -> None:
    await message.answer('Введи дату текстом в формате ДД.ММ.ГГГГ')


async def _show_stats_for_date(
    message: types.Message,
    container: Container,
    target_date: datetime,
) -> None:
    """Show statistics for all users for a specific date."""
    interactor: GetAllUsersStatsByDateInteractor = container.resolve(GetAllUsersStatsByDateInteractor)
    stats_list = await interactor.execute(date=target_date)

    date_str = target_date.strftime('%d.%m.%Y')

    if not stats_list:
        await message.answer(f'📊 Статистика за {date_str}:\n\nВ этот день никто не отжимался')
        return

    # Формируем текст с рейтингом
    medals = {1: '🥇', 2: '🥈', 3: '🥉'}
    stats_text = f'🏆 Статистика за {date_str}:\n\n'
    for idx, stats in enumerate(stats_list, start=1):
        medal = medals.get(idx, f'{idx}.')
        stats_text += f'{medal} @{stats.username}\nОтжиманий: {stats.total_count} ({stats.push_ups_count} подходов)\n\n'

    await message.answer(stats_text)

    # Отправляем видео каждого участника
    for stats in stats_list:
        if stats.videos:
            await message.answer(f'📹 Видео @{stats.username}:')
            for count, file_id, is_video_note in stats.videos:
                if is_video_note:
                    await message.answer_video_note(video_note=file_id)
                    await message.answer(f'@{stats.username}: {count} {pluralize_pushups(count)}')
                else:
                    await message.answer_video(
                        video=file_id,
                        caption=f'@{stats.username}: {count} {pluralize_pushups(count)}',
                    )


async def _notify_event_participants(
    bot: Bot,
    user: User,
    count: int,
    file_id: str,
    is_video_note: bool,
) -> None:
    """Send notification to group chats when user completes daily pushups."""
    try:
        async with get_async_session() as session:
            event_repository = EventRepository(session)
            chat_repository = ChatRepository(session)

            now = DatetimeProvider.provide()
            # Get active events where user is a participant
            active_events = await event_repository.get_active_events_by_participant(user.oid, now)

            if not active_events:
                return

            # Get active group chats
            active_chats = await chat_repository.get_many(is_active=True)
            if not active_chats:
                return

            for event in active_events:
                notification_text = (
                    f'🎉 @{user.username} выполнил дневную задачу!\n\n'
                    f'{event.str_info}\n'
                    f'💪 {count} {pluralize_pushups(count)}'
                )

                # Send to all active group chats
                for chat in active_chats:
                    logger.info(f'Sending notification to chat {chat.title} with id {chat.telegram_chat_id}')
                    try:
                        if is_video_note:
                            await bot.send_video_note(
                                chat_id=chat.telegram_chat_id,
                                video_note=file_id,
                            )
                            await bot.send_message(
                                chat_id=chat.telegram_chat_id,
                                text=notification_text,
                            )
                        else:
                            await bot.send_video(
                                chat_id=chat.telegram_chat_id,
                                video=file_id,
                                caption=notification_text,
                            )
                    except Exception as e:
                        # Group might have removed the bot or bot doesn't have permissions
                        logger.warning(f'Failed to send notification to chat {chat.telegram_chat_id}: {e}')

    except Exception as e:
        # Don't fail the main flow if notifications fail
        logger.error(f'Failed to send notifications: {e}')
