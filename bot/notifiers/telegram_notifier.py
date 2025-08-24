from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.bot.notifiers.abstract_notifier import AbstractNotifier


class TelegramNotifier(AbstractNotifier):
    def __init__(
            self,
            bot: Bot
    ) -> None:
        self.bot: Bot = bot

    async def notify(
            self,
            chat_id: int,
            text: str,
            document: BufferedInputFile | None = None,
            **kwargs
    ) -> bool:
        if document is not None:
            await self.bot.send_document(
                chat_id,
                document,
                caption=text
            )
        else:
            await self.bot.send_message(
                chat_id,
                text
            )

        return True

    @property
    def notify_method_name(self) -> str: return "telegram"
