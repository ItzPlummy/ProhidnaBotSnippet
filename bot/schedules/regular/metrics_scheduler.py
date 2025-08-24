import logging
from datetime import tzinfo, datetime, timedelta
from typing import List, Sequence

from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _
from pytz import timezone, utc
from sqlalchemy import select, true

from app.bot.classes.schedule_task import ScheduleTask
from app.bot.notifiers.abstract_notifier import AbstractNotifier
from app.bot.schedules.abstract_scheduler import AbstractScheduler
from app.database.database import Database
from app.database.models import Account, Settings, Role, AccountType, Metric
from app.services.config import Config


class MetricsScheduler(AbstractScheduler):
    def __init__(
            self,
            config: Config,
            database: Database,
            i18n: I18n,
            notifiers: List[AbstractNotifier]
    ) -> None:
        self.database: Database = database
        self.i18n: I18n = i18n
        self.current_timezone: tzinfo = timezone(config.timezone)
        self.notifiers: List[AbstractNotifier] = notifiers

        self.raspberry: bool = True
        self.readers: List[bool] = [True] * 4

    async def collect_tasks(self) -> List[ScheduleTask]:
        schedule_tasks: List[ScheduleTask] = []

        async with self.database.session_maker() as db:
            metrics: Sequence[Metric] = (
                await db.execute(
                    select(Metric)
                    .filter(Metric.created_at > datetime.now(utc) - timedelta(minutes=5))
                    .order_by(Metric.created_at.desc())
                    .limit(5)
                )
            ).scalars().all()

            if len(metrics):
                current_raspberry: bool = True
            else:
                current_raspberry = False

            current_readers: List[bool] = [True] * 4

            metric_datetime: datetime | None = None
            for metric in metrics:
                metric_datetime = metric.created_at
                if not metric.usb_0:
                    current_readers[0] = False
                if not metric.usb_1:
                    current_readers[1] = False
                if not metric.usb_2:
                    current_readers[2] = False
                if not metric.usb_3:
                    current_readers[3] = False

            metric_time: str = datetime.now(self.current_timezone).strftime("%H:%M")
            if metric_datetime is not None:
                metric_time = metric_datetime.astimezone(self.current_timezone).strftime("%H:%M")

            with self.i18n.context():
                if self.raspberry ^ current_raspberry:
                    if current_raspberry:
                        message_text: str = _("metrics.raspberry.working").format(time=metric_time)
                    else:
                        message_text: str = _("metrics.raspberry.broken").format(time=metric_time)
                elif self.readers != current_readers:
                    readers_list: List[str] = []

                    for index, current_reader in enumerate(current_readers):
                        if self.readers[index] ^ current_reader:
                            if current_reader:
                                readers_list.append(_("metrics.readers.working").format(index=index + 1))
                            else:
                                readers_list.append(_("metrics.readers.broken").format(index=index + 1))

                    message_text: str = _("metrics.readers.stats").format(
                        readers="\n".join(readers_list),
                        time=metric_time
                    )
                else:
                    self.raspberry = current_raspberry
                    self.readers = current_readers.copy()
                    return []

            administrators: Sequence[Account] = (
                await db.execute(
                    select(Account)
                    .join(Role)
                    .filter_by(account_type=AccountType.ADMINISTRATOR.name)
                    .join(Settings)
                    .filter(Settings.send_bot_messages.is_(true()))
                )
            ).unique().scalars().all()

            for administrator in administrators:
                for notifier in self.notifiers:
                    schedule_tasks.append(
                        ScheduleTask(
                            notifier.notify,
                            chat_id=administrator.telegram_id,
                            text=message_text
                        )
                    )

                    logging.getLogger("scheduler").info(
                        f"A task has been appended to send {administrator.full_name} "
                        f"a metric report by {notifier.notify_method_name}"
                    )

            self.raspberry = current_raspberry
            self.readers = current_readers.copy()

        return schedule_tasks
