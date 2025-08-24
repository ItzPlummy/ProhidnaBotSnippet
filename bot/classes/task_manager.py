import logging
from typing import Dict, Any, List
from uuid import uuid4

from click import UUID

from app.bot.classes.schedule_task import ScheduleTask


class TaskManager:
    def __init__(
            self,
            task_retry_amount: int
    ) -> None:
        self.tasks: Dict[UUID, ScheduleTask] = {}
        self.task_retry_amount: int = task_retry_amount

    async def add_tasks(
            self,
            tasks: List[ScheduleTask]
    ) -> None:
        for task in tasks:
            self.tasks[uuid4()] = task
            task.run()

    def remove_task(
            self,
            uuid: UUID
    ) -> None:
        if uuid in self.tasks:
            self.tasks.pop(uuid)

    async def inspect_tasks(self) -> None:
        for uuid, schedule_task in self.tasks.copy().items():
            if not schedule_task.task.done():
                continue
            try:
                result: Any = schedule_task.task.result()
                if result or schedule_task.retry_amount > self.task_retry_amount:
                    self.remove_task(uuid)
                else:
                    self.tasks[uuid].run()
            except Exception as e:
                logging.error(f"Task {uuid} raised an exception. Error: {e}")
                self.tasks[uuid].run()
