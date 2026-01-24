from punq import Container, Scope
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from btc_challenge.chats.adapters.sqlite.repository import ChatRepository
from btc_challenge.chats.application.interactors.create import CreateChatInteractor
from btc_challenge.chats.application.interactors.deactivate import DeactivateChatInteractor
from btc_challenge.chats.application.interactors.get_all import GetAllChatsInteractor
from btc_challenge.chats.domain.repository import IChatRepository
from btc_challenge.events.adapters.sqlite.repository import EventRepository
from btc_challenge.events.application.interactors.complete import CompleteEventInteractor
from btc_challenge.events.application.interactors.create import CreateEventInteractor
from btc_challenge.events.application.interactors.get_participants import GetEventParticipantsInteractor
from btc_challenge.events.application.interactors.join import JoinEventInteractor
from btc_challenge.events.domain.repository import IEventRepository
from btc_challenge.push_ups.adapters.sqlite.repository import PushUpRepository
from btc_challenge.push_ups.application.interactors.create import CreatePushUpInteractor
from btc_challenge.push_ups.application.interactors.get_all_users_stats import GetAllUsersStatsInteractor
from btc_challenge.push_ups.application.interactors.get_all_users_stats_by_date import (
    GetAllUsersStatsByDateInteractor,
)
from btc_challenge.push_ups.application.interactors.get_daily_stats import GetDailyStatsInteractor
from btc_challenge.push_ups.domain.repository import IPushUpRepository
from btc_challenge.shared.adapters.sqlite.commiter import Commiter
from btc_challenge.shared.adapters.sqlite.session import get_async_sessionmaker
from btc_challenge.shared.application.commiter import ICommiter
from btc_challenge.stored_object.adapters.sqlite.repository import StoredObjectRepository
from btc_challenge.stored_object.domain.repository import IStoredObjectRepository
from btc_challenge.users.adapters.sqlite.repository import UserRepository
from btc_challenge.users.application.interactors.create import CreateUserInteractor
from btc_challenge.users.application.interactors.get_one import GetUserByTelegramIdInteractor
from btc_challenge.users.application.interactors.verify import VerifyUserInteractor
from btc_challenge.users.domain.repository import IUserRepository


def build_container() -> Container:
    container = Container()

    # Infrastructure - singletons
    container.register(async_sessionmaker[AsyncSession], instance=get_async_sessionmaker(), scope=Scope.singleton)
    # container.register(IS3Storage, instance=init_minio_storage(), scope=Scope.singleton)

    # Repositories - transient
    container.register(ICommiter, Commiter)
    container.register(IUserRepository, UserRepository)
    container.register(IPushUpRepository, PushUpRepository)
    container.register(IStoredObjectRepository, StoredObjectRepository)
    container.register(IEventRepository, EventRepository)
    container.register(IChatRepository, ChatRepository)

    # Interactors - transient
    container.register(CreateUserInteractor)
    container.register(VerifyUserInteractor)
    container.register(CreatePushUpInteractor)
    container.register(GetDailyStatsInteractor)
    container.register(GetAllUsersStatsInteractor)
    container.register(GetAllUsersStatsByDateInteractor)
    container.register(GetUserByTelegramIdInteractor)
    container.register(CreateEventInteractor)
    container.register(JoinEventInteractor)
    container.register(GetEventParticipantsInteractor)
    container.register(CompleteEventInteractor)
    container.register(CreateChatInteractor)
    container.register(DeactivateChatInteractor)
    container.register(GetAllChatsInteractor)

    return container


def build_request_container(container: Container, session: AsyncSession) -> Container:
    container.register(AsyncSession, instance=session)
    return container
