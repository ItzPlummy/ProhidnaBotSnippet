import logging
import random
from datetime import tzinfo, datetime, time
from typing import List, Sequence

from aiogram import html
from aiogram.utils.i18n import I18n
from pytz import timezone, utc
from sqlalchemy import select, true, func
from sqlalchemy.orm import joinedload

from app.bot.classes.schedule_task import ScheduleTask
from app.bot.notifiers.abstract_notifier import AbstractNotifier
from app.bot.schedules.abstract_scheduler import AbstractScheduler
from app.bot.variations.variation_type import VariationType
from app.bot.variations.variations import variations
from app.database.database import Database
from app.database.models import Entry, Student, Account, Settings, StudentsParents
from app.services.config import Config


class EntersScheduler(AbstractScheduler):
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

    async def collect_tasks(self) -> List[ScheduleTask]:
        schedule_tasks: List[ScheduleTask] = []

        async with self.database.session_maker() as db:
            now: datetime = datetime.now(utc)

            entries: Sequence[Entry] = (
                await db.execute(
                    select(Entry)
                    .filter(
                        Entry.notified_at.is_(None),
                        func.date(Entry.passing_time) == now.date()
                    )
                    .join(Student)
                    .join(StudentsParents)
                    .join(Account)
                    .filter(Account.telegram_id.is_not(None))
                    .join(Settings)
                    .filter(Settings.send_bot_messages.is_(true()))
                    .options(
                        joinedload(Entry.student).joinedload(Student.parents).joinedload(Account.settings)
                    )
                )
            ).unique().scalars().all()

            with self.i18n.context():
                for entry in entries:
                    entry.notified_at = now
                    passing_time: datetime = entry.passing_time.replace(tzinfo=utc).astimezone(self.current_timezone)

                    for parent in entry.student.parents:
                        if parent.telegram_id is None:
                            continue

                        message_text: str = variations.get_enter_variation(
                            parent.settings.allow_bot_variations if parent.settings is not None else False,
                            entry.has_entered,
                            VariationType.get_variation_type(passing_time)
                        ).format(full_name=html.quote(entry.student.full_name))

                        if not (0 <= (entry.created_at - entry.passing_time).seconds <= 60):
                            message_text = f"<i>{html.quote(passing_time.strftime('%H:%M'))}</i>\n{message_text}"

                        if entry.passing_time.time() > time(hour=6, minute=30) and random.random() < 0.15:
                            message_text += "\n\nШановні батьки! Нагадуємо, що навчання в ліцеї починається о 8:30, але всі учні мають бути присутні о 8:15. Дякуємо за розуміння!"

                        for notifier in self.notifiers:
                            schedule_tasks.append(
                                ScheduleTask(
                                    notifier.notify,
                                    chat_id=parent.telegram_id,
                                    text=message_text
                                )
                            )

                            logging.getLogger("scheduler").info(
                                f"A task has been appended to send {parent.full_name} "
                                f"an entry details of {entry.student.full_name} "
                                f"by {notifier.notify_method_name}"
                            )

                await db.commit()

        return schedule_tasks
