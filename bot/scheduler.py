import asyncio
import logging
import sys
from typing import List

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.i18n import I18n

from app.bot.classes.schedule_manager import ScheduleManager
from app.bot.notifiers.abstract_notifier import AbstractNotifier
from app.bot.notifiers.telegram_notifier import TelegramNotifier
from app.bot.schedules.daily.daily_late_logs_scheduler import DailyLateLogsScheduler
from app.bot.schedules.daily.daily_present_logs_scheduler import DailyPresentLogsScheduler
from app.bot.schedules.daily.daily_stats_scheduler import DailyStatsScheduler
from app.bot.schedules.regular.enters_scheduler import EntersScheduler
from app.bot.schedules.regular.metrics_scheduler import MetricsScheduler
from app.bot.schedules.weekly.weekly_antirating_scheduler import WeeklyAntiRatingScheduler
from app.bot.schedules.weekly.weekly_group_antirating_scheduler import WeeklyGroupAntiRatingScheduler
from app.database.database import Database, create_db
from app.services.config import Config

config: Config = Config(_env_file=".env")

bot: Bot = Bot(
    token=config.telegram_token.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)


async def main() -> None:
    logger: logging.Logger = logging.getLogger("schedule_logger")
    logger.setLevel(logging.INFO)

    database: Database = create_db(str(config.postgresql_dsn))
    i18n: I18n = I18n(
        path=config.locale_path,
        default_locale=config.locale,
        domain=config.domain
    )
    notifiers: List[AbstractNotifier] = [
        TelegramNotifier(bot)
    ]

    scheduler: ScheduleManager = ScheduleManager(
        EntersScheduler(
            config,
            database,
            i18n,
            notifiers
        ),
        MetricsScheduler(
            config,
            database,
            i18n,
            notifiers
        ),
        DailyPresentLogsScheduler(
            config,
            database,
            i18n,
            notifiers
        ),
        DailyLateLogsScheduler(
            config,
            database,
            i18n,
            notifiers
        ),
        DailyStatsScheduler(
            config,
            database,
            i18n,
            notifiers
        ),
        WeeklyAntiRatingScheduler(
            config,
            database,
            i18n,
            notifiers
        ),
        WeeklyGroupAntiRatingScheduler(
            config,
            database,
            i18n,
            notifiers
        )
    )

    await scheduler.start_schedule()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(asctime)s - %(message)s",
        datefmt="%d-%m-%y %H:%M:%S"
    )

    asyncio.run(main())
