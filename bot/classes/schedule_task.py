import asyncio
from asyncio import Task
from typing import Any, Tuple, Dict


class ScheduleTask:
    def __init__(
            self,
            coroutine: Any,
            *args: Any,
            **kwargs: Any
    ) -> None:
        self.coroutine: Any = coroutine
        self.args: Tuple[Any, ...] = args
        self.kwargs: Dict[str, Any] = kwargs

        self.task: Task | None = None
        self.retry_amount: int = -1

    def run(self) -> None:
        if self.task is not None and not self.task.done():
            return

        self.task = asyncio.create_task(self.coroutine(*self.args, **self.kwargs))
        self.retry_amount += 1
