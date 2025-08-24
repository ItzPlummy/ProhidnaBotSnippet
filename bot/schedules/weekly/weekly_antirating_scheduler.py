import logging
from datetime import time, datetime, timedelta, date
from typing import List, Sequence

from aiogram.types import BufferedInputFile
from aiogram.utils.i18n import I18n
from pytz import timezone, utc
from sqlalchemy import select, true, or_

from app.bot.classes.schedule_task import ScheduleTask
from app.bot.enums.account_type import AccountType
from app.bot.notifiers.abstract_notifier import AbstractNotifier
from app.bot.schedules.abstract_scheduler import AbstractScheduler
from app.bot.schedules.timestamps.weekly_timestamp import WeeklyTimestamp
from app.bot.schedules.weekly.weekly_scheduler import WeeklyScheduler
from app.database.database import Database
from app.database.models import Account, Settings, Role
from app.services.config import Config
from app.statistics.antirating_creator import AntiRatingCreator
from app.statistics.models.antirating_report_model import AntiRatingReportModel


class WeeklyAntiRatingScheduler(WeeklyScheduler, AbstractScheduler):
    def __init__(
            self,
            config: Config,
            database: Database,
            i18n: I18n,
            notifiers: List[AbstractNotifier]
    ) -> None:
        self.database: Database = database
        self.notifiers: List[AbstractNotifier] = notifiers

        self.antirating_creator: AntiRatingCreator = AntiRatingCreator(database, i18n, timezone(config.timezone))

        self.start_time: time = datetime.strptime(config.school_day_start_time, "%H:%M").time()
        self.antirating_time: time = datetime.strptime(config.schedule_antirating_time, "%H:%M").time()

        super().__init__(WeeklyTimestamp(weekday=4, time=self.antirating_time))

    async def collect_tasks(self) -> List[ScheduleTask]:
        schedule_tasks: List[ScheduleTask] = []

        if not self.do_send_logs():
            return schedule_tasks

        async with self.database.session_maker() as db:
            accounts: Sequence[Account] = (
                await db.execute(
                    select(Account).
                    filter(Account.telegram_id.is_not(None)).
                    join(Settings).
                    filter(Settings.send_bot_messages.is_(true())).
                    join(Role).
                    filter(
                        or_(
                            Role.account_type == AccountType.ADMINISTRATOR.name,
                            Role.account_type == AccountType.MANAGER.name
                        )
                    )
                )
            ).unique().scalars().all()

        weekday: int = datetime.now(utc).weekday()

        date_range: List[date] = [
            (datetime.now(utc) - timedelta(days=index)).date()
            for index in range(weekday, -1, -1)
        ]

        antirating_model: AntiRatingReportModel = await self.antirating_creator.create_antirating(
            self.start_time,
            10,
            date_range
        )

        for account in accounts:
            for notifier in self.notifiers:
                schedule_tasks.append(
                    ScheduleTask(
                        notifier.notify,
                        chat_id=account.telegram_id,
                        text=antirating_model.message,
                        document=BufferedInputFile(
                            antirating_model.xlsx_file,
                            antirating_model.filename
                        )
                    )
                )

                logging.getLogger("scheduler").info(
                    f"A task has been appended to send {account.full_name} "
                    f"weekly antirating by {notifier.notify_method_name}"
                )

        return schedule_tasks
