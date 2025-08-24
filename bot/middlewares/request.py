import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject, Update
from aiogram.utils.i18n import gettext as _, I18n
from aiohttp import ClientConnectionError

from app.bot.requests.request_manager import RequestManager


class RequestMiddleware(BaseMiddleware):
    def __init__(
            self,
            request_manager: RequestManager,
            i18n: I18n
    ) -> None:
        self.request_manager = request_manager
        self.i18n = i18n

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        data["request_manager"] = self.request_manager

        try:
            return await handler(event, data)
        except ClientConnectionError as e:
            logging.error(e)

            if isinstance(event, Update):
                if event.callback_query is not None:
                    try:
                        with self.i18n.context():
                            await event.callback_query.answer(_("exception.server_error"), show_alert=False)
                    except TelegramBadRequest:
                        pass

                if event.message is not None:
                    with self.i18n.context():
                        message = await event.message.reply(_("exception.server_error"))

                    await asyncio.sleep(5)
                    await message.delete()
