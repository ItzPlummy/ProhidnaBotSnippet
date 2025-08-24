import asyncio
import logging
import sys
from datetime import time, datetime, tzinfo

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.scene import SceneRegistry
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.i18n import ConstI18nMiddleware, I18n
from pytz import timezone
from redis.asyncio import Redis

from app.bot.classes.button_factory import ButtonFactory
from app.bot.classes.dict_factory import DictFactory
from app.bot.classes.identifier import Identifier
from app.bot.classes.temp_message_manager import TempMessageManager
from app.bot.middlewares.database import DatabaseMiddleware
from app.bot.middlewares.identify import IdentifyMiddleware
from app.bot.routers.start_command_router import start_command_router
from app.bot.scenes.admin_scene import AdminScene
from app.bot.scenes.announcement.announcement_group_scene import AnnouncementGroupScene
from app.bot.scenes.announcement.announcement_scene import AnnouncementScene
from app.bot.scenes.contact_scene import ContactScene
from app.bot.scenes.disable_scene import DisableScene
from app.bot.scenes.entries.entries_calendar_scene import EntriesCalendarScene
from app.bot.scenes.entries.entries_scene import EntriesScene
from app.bot.scenes.log.log_calendar_scene import LogCalendarScene
from app.bot.scenes.log.log_scene import LogScene
from app.bot.scenes.note.send_note_calendar_scene import SendNoteCalendarScene
from app.bot.scenes.stats.stats_calendar_scene import StatsCalendarScene
from app.bot.scenes.stats.stats_group_scene import StatsGroupScene
from app.bot.scenes.stats.stats_scene import StatsScene
from app.bot.scenes.note.send_note_scene import SendNoteScene
from app.bot.scenes.note.send_note_student_scene import SendNoteStudentScene
from app.bot.scenes.settings_scene import SettingsScene
from app.bot.scenes.start_scene import StartScene
from app.database.database import create_db, Database
from app.services.config import Config
from app.statistics.data.data_creator import DataCreator
from app.statistics.date_manager import DateManager
from app.statistics.entries_creator import EntriesCreator
from app.statistics.logs_creator import LogsCreator

config = Config(_env_file=".env")

bot = Bot(
    token=config.telegram_token.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)


def create_dispatcher() -> Dispatcher:
    redis: Redis | None = None
    storage: RedisStorage | None = None

    if config.redis_storage_dsn is not None:
        redis = Redis.from_url(str(config.redis_storage_dsn))
        storage = RedisStorage(redis, key_builder=DefaultKeyBuilder(with_destiny=True))

    new_dispatcher = Dispatcher(storage=storage)

    database: Database = create_db(str(config.postgresql_dsn))
    i18n: I18n = I18n(path=config.locale_path, default_locale=config.locale, domain=config.domain)
    temp: TempMessageManager = TempMessageManager(bot, redis)
    start_time: time = datetime.strptime(config.school_day_start_time, "%H:%M").time()
    current_timezone: tzinfo = timezone(config.timezone)
    dict_factory: DictFactory = DictFactory(i18n)
    button_factory: ButtonFactory = ButtonFactory(i18n)
    date_manager: DateManager = DateManager()

    data_creator: DataCreator = DataCreator(database)
    entries_creator: EntriesCreator = EntriesCreator(
        database,
        i18n,
        current_timezone
    )
    logs_creator: LogsCreator = LogsCreator(
        database,
        i18n,
        current_timezone
    )

    new_dispatcher.workflow_data.update(
        {
            "config": config,
            "database": database,
            "i18n": i18n,
            "temp": temp,
            "start_time": start_time,
            "current_timezone": current_timezone,
            "dict_factory": dict_factory,
            "button_factory": button_factory,
            "date_manager": date_manager,
            "data_creator": data_creator,
            "entries_creator": entries_creator,
            "logs_creator": logs_creator,
        }
    )

    new_dispatcher.update.outer_middleware.register(DatabaseMiddleware(database))
    new_dispatcher.update.outer_middleware.register(IdentifyMiddleware(Identifier()))
    ConstI18nMiddleware(i18n=i18n, locale=config.locale).setup(new_dispatcher)

    new_dispatcher.include_routers(start_command_router)

    registry = SceneRegistry(new_dispatcher)
    registry.add(
        StartScene,
        EntriesScene,
        LogScene,
        StatsScene,
        StatsGroupScene,
        EntriesCalendarScene,
        LogCalendarScene,
        StatsCalendarScene,
        AnnouncementGroupScene,
        SettingsScene,
        DisableScene,
        ContactScene,
        AdminScene,
        AnnouncementScene,
        SendNoteScene,
        SendNoteStudentScene,
        SendNoteCalendarScene
    )

    return new_dispatcher


async def main() -> None:
    dispatcher = create_dispatcher()

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(asctime)s - %(message)s",
        datefmt="%d-%m-%y %H:%M:%S"
    )

    asyncio.run(main())
