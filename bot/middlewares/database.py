from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.database import Database


class DatabaseMiddleware(BaseMiddleware):
    def __init__(
            self,
            database: Database
    ) -> None:
        self.database = database

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        async with self.database.session_maker() as session:
            data["db"] = session
            return await handler(event, data)
