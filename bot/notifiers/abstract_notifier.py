from abc import ABC, abstractmethod
from typing import Any


class AbstractNotifier(ABC):
    @abstractmethod
    async def notify(
            self,
            **kwargs: Any
    ) -> None:
        pass

    @property
    @abstractmethod
    def notify_method_name(self) -> str: pass
