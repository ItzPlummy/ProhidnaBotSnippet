from datetime import datetime, time
from typing import Tuple

from pytz import utc

from app.bot.schedules.timestamps.weekly_timestamp import WeeklyTimestamp


class WeeklyScheduler:
    def __init__(
            self,
            *timestamps: WeeklyTimestamp
    ) -> None:
        self.timestamps: Tuple[WeeklyTimestamp, ...] = timestamps

    def do_send_logs(self) -> bool:
        do_send: bool = False

        for timestamp in self.timestamps:
            if (
                    timestamp.weekday == datetime.now(utc).weekday()
                    and timestamp.time.hour == datetime.now(utc).hour
                    and timestamp.time.minute == datetime.now(utc).minute
                    and not timestamp.is_logged
            ):
                timestamp.is_logged = True
                do_send = True

            if timestamp.time > datetime.now(utc).time() or timestamp.time < time(hour=0, minute=1):
                timestamp.is_logged = False

        return do_send
