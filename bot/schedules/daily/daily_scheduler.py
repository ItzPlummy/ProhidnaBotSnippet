from datetime import datetime, time
from typing import Tuple

from pytz import utc

from app.bot.schedules.timestamps.daily_timestamp import DailyTimestamp


class DailyScheduler:
    def __init__(
            self,
            *timestamps: DailyTimestamp,
            log_on_weekends: bool
    ) -> None:
        self.timestamps: Tuple[DailyTimestamp, ...] = timestamps
        self.log_on_weekends: bool = log_on_weekends

    def do_send_logs(self) -> bool:
        if datetime.now(utc).weekday() >= 5 and not self.log_on_weekends:
            return False

        do_send: bool = False

        for timestamp in self.timestamps:
            if (
                    timestamp.time.hour == datetime.now(utc).hour
                    and timestamp.time.minute == datetime.now(utc).minute
                    and not timestamp.is_logged
            ):
                timestamp.is_logged = True
                do_send = True

            if timestamp.time > datetime.now(utc).time() or timestamp.time < time(hour=0, minute=1):
                timestamp.is_logged = False

        return do_send
