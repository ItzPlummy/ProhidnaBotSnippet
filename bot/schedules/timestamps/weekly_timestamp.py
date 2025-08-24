from datetime import time

from pydantic import BaseModel


class WeeklyTimestamp(BaseModel):
    weekday: int
    time: time
    is_logged: bool = False
