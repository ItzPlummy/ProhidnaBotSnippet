import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from app.bot.scenes.base.base_scene import BaseScene
from app.bot.scenes.callback_data import SendAction


class SendScene(BaseScene, ABC):
    @abstractmethod
    async def on_callback_query_enter(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    async def on_message(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    async def on_send(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @on.callback_query.enter()
    async def __on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            state: FSMContext,
            **kwargs
    ) -> None:
        await asyncio.create_task(state.update_data(message_id=callback_query.message.message_id))

        await self._prepare_func(
            self.on_callback_query_enter,
            callback_query=callback_query,
            state=state,
            **kwargs
        )

    @on.message()
    async def __on_message(
            self,
            message: Message,
            state: FSMContext,
            **kwargs
    ) -> None:
        await message.delete()
        await asyncio.create_task(state.update_data(text=message.text))

        data: Dict[str, Any] = await state.get_data()
        message_id: int = data.get("message_id")

        await self._prepare_func(
            self.on_message,
            message=message,
            message_id=message_id,
            text=message.text,
            state=state,
            data=data,
            **kwargs
        )

    @on.callback_query(SendAction.filter())
    async def __on_send(
            self,
            callback_query: CallbackQuery,
            state: FSMContext,
            **kwargs
    ) -> None:
        data: Dict[str, Any] = await state.get_data()
        message_id: int = data.get("message_id")
        text: str = data.get("text")

        if text is None:
            await callback_query.answer(_("answer.no_message"), show_alert=False)
            return

        await self._prepare_func(
            self.on_send,
            callback_query=callback_query,
            message_id=message_id,
            text=text,
            state=state,
            data=data,
            **kwargs
        )
