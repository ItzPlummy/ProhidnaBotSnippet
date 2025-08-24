import logging
from datetime import time, datetime
from typing import List

from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _
from pytz import timezone
from pyuca import Collator

from app.bot.classes.schedule_task import ScheduleTask
from app.bot.notifiers.abstract_notifier import AbstractNotifier
from app.bot.schedules.abstract_scheduler import AbstractScheduler
from app.bot.schedules.daily.daily_scheduler import DailyScheduler
from app.bot.schedules.timestamps.daily_timestamp import DailyTimestamp
from app.bot.variations.variation_type import VariationType
from app.bot.variations.variations import variations
from app.database.database import Database
from app.services.config import Config
from app.statistics.models.late_report_model import LateReportModel
from app.statistics.reports_creator import ReportsCreator

collator: Collator = Collator()


class DailyLateLogsScheduler(DailyScheduler, AbstractScheduler):
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
        self.i18n: I18n = i18n
        self.notifiers: List[AbstractNotifier] = notifiers

        self.reports_creator: ReportsCreator = ReportsCreator(database, i18n, timezone(config.timezone))

        self.start_time: time = datetime.strptime(config.school_day_start_time, "%H:%M").time()
        self.log_time: time = datetime.strptime(config.schedule_late_log_time, "%H:%M").time()

        super().__init__(DailyTimestamp(time=self.log_time), log_on_weekends=log_on_weekends)

    async def collect_tasks(self) -> List[ScheduleTask]:
        schedule_tasks: List[ScheduleTask] = []

        if not self.do_send_logs():
            return schedule_tasks

        report_entries: List[LateReportModel] = await self.reports_creator.create_late_reports(self.start_time)

        for report_entry in report_entries:
            if report_entry.is_empty:
                with self.i18n.context():
                    message: str = _("log.no_one_late")
            else:
                message: str = variations.get_log_variation(
                    report_entry.supervisor.settings.allow_bot_variations
                    if report_entry.supervisor.settings is not None else False,
                    VariationType.LATE
                ).format(
                    late=report_entry.lateness_message,
                    info=report_entry.group.name
                )

            for notifier in self.notifiers:
                schedule_tasks.append(
                    ScheduleTask(
                        notifier.notify,
                        chat_id=report_entry.supervisor.telegram_id,
                        text=message
                    )
                )

                logging.getLogger("scheduler").info(
                    f"A task has been appended to send {report_entry.supervisor.full_name} "
                    f"daily logs of all present students from {report_entry.group.name} "
                    f"by {notifier.notify_method_name}"
                )

        return schedule_tasks
