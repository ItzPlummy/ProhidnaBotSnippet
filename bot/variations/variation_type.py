from datetime import datetime
from enum import Enum


class VariationType(Enum):
    DEFAULT = "default"
    NIGHT = "night"

    PRESENT = "present"
    LATE = "late"

    @classmethod
    def get_variation_type(cls, current_time: datetime):
        if current_time.hour <= 4 or current_time.hour >= 21:
            return cls.NIGHT

        return cls.DEFAULT
