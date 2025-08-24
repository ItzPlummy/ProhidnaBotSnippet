from abc import ABC, abstractmethod
from typing import Any

from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery

from app.bot.scenes.base.base_scene import BaseScene
from app.bot.scenes.callback_data import PageAction


class PageScene(BaseScene, ABC):
    @abstractmethod
    async def on_page_turn(
            self,
            *args: Any,
            **kwargs: Any
    ) -> None: pass

    @on.callback_query(PageAction.filter())
    async def __on_page_turn(
            self,
            callback_query: CallbackQuery,
            callback_data: PageAction,
            **kwargs: Any
    ) -> None:
        page: int = callback_data.page

        await self._prepare_func(
            self.on_page_turn,
            callback_query=callback_query,
            page=page,
            **kwargs
        )
