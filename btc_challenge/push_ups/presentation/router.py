from io import BytesIO

from aiogram import Bot, F, Router, filters, types
from aiogram.fsm.context import FSMContext
from punq import Container

from btc_challenge.push_ups.application.interactors.create import CreatePushUpInteractor
from btc_challenge.push_ups.application.interactors.get_all_users_stats import GetAllUsersStatsInteractor
from btc_challenge.push_ups.application.interactors.get_daily_stats import GetDailyStatsInteractor
from btc_challenge.push_ups.presentation.states import PushUpStates
from btc_challenge.shared.errors import ObjectNotFoundError

push_ups_router = Router()


@push_ups_router.message(filters.Command("add", "push_up"))
async def cmd_add_push_up(message: types.Message, state: FSMContext) -> None:
    await state.set_state(PushUpStates.waiting_for_count)
    await message.answer("Сколько отжиманий сделал?")


@push_ups_router.message(PushUpStates.waiting_for_count, F.text)
async def process_count(message: types.Message, state: FSMContext) -> None:
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
async def process_video(message: types.Message, state: FSMContext, bot: Bot, container: Container) -> None:
    if not message.from_user:
        return

    user_id = message.from_user.id
    data = await state.get_data()
    count = data.get("count", 0)

    # Определяем тип файла и получаем объект
    file: types.Video | types.VideoNote | None = None
    if message.video:
        file = message.video
        file_name = file.file_name or f"video_{file.file_id}.mp4"
        extension = ".mp4"
    elif message.video_note:
        file = message.video_note
        file_name = f"video_note_{file.file_id}.mp4"
        extension = ".mp4"
    else:
        return

    # Скачиваем файл из Telegram
    file_info = await bot.get_file(file.file_id)
    file_bytes = BytesIO()
    if not file_info.file_path:
        return
    await bot.download_file(file_info.file_path, file_bytes)
    file_data = file_bytes.getvalue()

    # Сохраняем в БД и MinIO
    interactor = container.resolve(CreatePushUpInteractor)
    await interactor.execute(
        telegram_id=user_id,
        file_data=file_data,
        file_name=file_name,
        extension=extension,
        count=count,
    )

    await state.clear()
    await message.answer(f"Подход сохранен! {count} отжиманий 💪")


@push_ups_router.message(PushUpStates.waiting_for_video)
async def wrong_video_type(message: types.Message) -> None:
    await message.answer("Отправь видео или кружок с подтверждением")


@push_ups_router.message(filters.Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять")
        return

    await state.clear()
    await message.answer("Отменил")


@push_ups_router.message(filters.Command("info"))
async def cmd_info(message: types.Message, container: Container) -> None:
    if not message.from_user:
        return

    user_id = message.from_user.id

    interactor = container.resolve(GetDailyStatsInteractor)
    try:
        stats = await interactor.execute(telegram_id=user_id)
    except ObjectNotFoundError:
        await message.answer("Сначала нажми /start")
        return

    if stats.push_ups_count == 0:
        await message.answer("Сегодня еще не было подходов")
        return

    # Отправляем статистику
    stats_text = f"📊 Статистика за сегодня:\n\nВсего отжиманий: {stats.total_count}\nПодходов: {stats.push_ups_count}"
    await message.answer(stats_text)

    # Отправляем видео
    for count, video_bytes in stats.videos:
        video_file = types.BufferedInputFile(video_bytes, filename="video.mp4")
        await message.answer_video(
            video=video_file,
            caption=f"Подход: {count} отжиманий",
        )


@push_ups_router.message(filters.Command("stats", "leaderboard"))
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
