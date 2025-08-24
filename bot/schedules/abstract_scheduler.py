from abc import ABC, abstractmethod
from typing import List

from app.bot.classes.schedule_task import ScheduleTask


class AbstractScheduler(ABC):
    @abstractmethod
    async def collect_tasks(self) -> List[ScheduleTask]:
        pass
