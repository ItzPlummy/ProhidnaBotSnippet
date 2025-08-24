from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.bot.classes.identifier import Identifier


class IdentifyMiddleware(BaseMiddleware):
    """
    Identifier is not transferred in the DependencyMiddleware as others cause
    in future it may have more functionality than just being in the handler parameters
    """

    def __init__(
            self,
            identifier: Identifier
    ) -> None:
        self.identifier = identifier

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        data["identifier"] = self.identifier
        return await handler(event, data)
