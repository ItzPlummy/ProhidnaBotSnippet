from datetime import time

from pydantic import BaseModel


class DailyTimestamp(BaseModel):
    time: time
    is_logged: bool = False
