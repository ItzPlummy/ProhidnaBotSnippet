import asyncio
import time
import logging
from typing import Tuple

from aiogram import Bot

from app.bot.classes.task_manager import TaskManager
from app.bot.schedules.abstract_scheduler import AbstractScheduler


class ScheduleManager:
    def __init__(
            self,
            *schedulers: AbstractScheduler,
            task_execution_delay: float = 10,
            task_retry_amount: int = 10
    ):
        self.schedulers: Tuple[AbstractScheduler, ...] = schedulers

        self.task_manager: TaskManager = TaskManager(task_retry_amount)
        self.task_execution_delay: float = task_execution_delay
        self.bot: Bot | None = None

    async def start_schedule(self):
        logging.getLogger("scheduler").setLevel(logging.INFO)
        logging.getLogger("scheduler").info("Start scheduling")
        logger = logging.getLogger("scheduler")
        logger.setLevel(logging.INFO)
        logger.info("Start scheduling")
        started_func_time = time.monotonic()
        logger.info("Started start_schedule %i", started_func_time)

        while True:
            start_cycle = time.monotonic()
            logger.info(f"Start schedule cycle of collection tasks: {start_cycle - started_func_time}")
            for scheduler in self.schedulers:
                 await self.task_manager.add_tasks(await scheduler.collect_tasks())
                 logger.info(f"Ended collection tasks from {type(scheduler)} in {time.monotonic() - start_cycle}")

            await asyncio.sleep(self.task_execution_delay)
            await self.task_manager.inspect_tasks()
       
