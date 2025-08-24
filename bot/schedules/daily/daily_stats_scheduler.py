import logging
from datetime import time, datetime
from typing import List, Sequence

from aiogram.types import BufferedInputFile
from aiogram.utils.i18n import I18n
from pytz import timezone
from pyuca import Collator
from sqlalchemy import select, true, or_

from app.api.v2.enums.account_type import AccountType
from app.bot.classes.schedule_task import ScheduleTask
from app.bot.notifiers.abstract_notifier import AbstractNotifier
from app.bot.schedules.abstract_scheduler import AbstractScheduler
from app.bot.schedules.daily.daily_scheduler import DailyScheduler
from app.bot.schedules.timestamps.daily_timestamp import DailyTimestamp
from app.database.database import Database
from app.database.models import Account, Settings, Role
from app.services.config import Config
from app.statistics.models.statistics_report_model import StatisticsReportModel
from app.statistics.statistics_creator import StatisticsCreator

collator: Collator = Collator()


class DailyStatsScheduler(DailyScheduler, AbstractScheduler):
    def __init__(
            self,
            config: Config,
            database: Database,
            i18n: I18n,
            notifiers: List[AbstractNotifier],
            *,
            log_on_weekends: bool = False
    ) -> None:
        self.database: Database = database
        self.notifiers: List[AbstractNotifier] = notifiers

        self.statistics_creator: StatisticsCreator = StatisticsCreator(database, i18n, timezone(config.timezone))

        self.start_time: time = datetime.strptime(config.school_day_start_time, "%H:%M").time()
        self.stats_time: time = datetime.strptime(config.schedule_stats_time, "%H:%M").time()

        super().__init__(
            DailyTimestamp(time=self.stats_time),
            log_on_weekends=log_on_weekends
        )

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

        statistics_model: StatisticsReportModel = await self.statistics_creator.create_statistics(self.start_time)

        for account in accounts:
            for notifier in self.notifiers:
                schedule_tasks.append(
                    ScheduleTask(
                        notifier.notify,
                        chat_id=account.telegram_id,
                        text=statistics_model.message,
                        document=BufferedInputFile(
                            statistics_model.xlsx_file,
                            statistics_model.filename
                        )
                    )
                )

                logging.getLogger("scheduler").info(
                    f"A task has been appended to send {account.full_name} "
                    f"daily statistics by {notifier.notify_method_name}"
                )

        return schedule_tasks
