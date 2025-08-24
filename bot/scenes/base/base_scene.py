from datetime import tzinfo, time
from inspect import getfullargspec
from typing import Callable, Any, Dict, Awaitable

from aiogram.fsm.scene import Scene, on
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import I18n

from app.bot.classes.button_factory import ButtonFactory
from app.bot.classes.dict_factory import DictFactory
from app.bot.classes.temp_message_manager import TempMessageManager
from app.bot.scenes.abstract_scene import AbstractScene
from app.bot.scenes.callback_data import BackAction, ChangeSceneAction, MenuAction
from app.database.database import Database
from app.services.config import Config
from app.statistics.data.data_creator import DataCreator
from app.statistics.date_manager import DateManager
from app.statistics.entries_creator import EntriesCreator
from app.statistics.logs_creator import LogsCreator


class BaseScene(Scene, AbstractScene):
    def __init__(
            self,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self.config: Config = self.wizard.data["config"]
        self.database: Database = self.wizard.data["database"]
        self.i18n: I18n = self.wizard.data["i18n"]
        self.temp: TempMessageManager = self.wizard.data["temp"]
        self.start_time: time = self.wizard.data["start_time"]
        self.timezone: tzinfo = self.wizard.data["current_timezone"]
        self.dict_factory: DictFactory = self.wizard.data["dict_factory"]
        self.button_factory: ButtonFactory = self.wizard.data["button_factory"]
        self.date_manager: DateManager = self.wizard.data["date_manager"]
        self.data_creator: DataCreator = self.wizard.data["data_creator"]
        self.entries_creator: EntriesCreator = self.wizard.data["entries_creator"]
        self.logs_creator: LogsCreator = self.wizard.data["logs_creator"]

    async def on_menu(
            self,
            **kwargs
    ) -> None:
        await self.wizard.goto("start")

    async def on_back(
            self,
            **kwargs
    ) -> None:
        await self.wizard.back()

    async def on_scene_change(
            self,
            callback_data: ChangeSceneAction,
            **kwargs
    ) -> None:
        await self.wizard.goto(callback_data.to_scene)

    @on.callback_query(MenuAction.filter())
    async def __on_menu(
            self,
            callback_query: CallbackQuery,
            **kwargs
    ) -> None:
        await self._prepare_func(
            self.on_menu,
            callback_query=callback_query,
            **kwargs
        )

    @on.callback_query(BackAction.filter())
    async def __on_back(
            self,
            callback_query: CallbackQuery,
            **kwargs
    ) -> None:
        if await self.wizard.state.get_state() != "start":
            await self._prepare_func(
                self.on_back,
                callback_query=callback_query,
                **kwargs
            )

    @on.callback_query(ChangeSceneAction.filter())
    async def __on_scene_change(
            self,
            callback_query: CallbackQuery,
            callback_data: ChangeSceneAction,
            **kwargs
    ) -> None:
        await self._prepare_func(
            self.on_scene_change,
            callback_query=callback_query,
            callback_data=callback_data,
            **kwargs
        )

    @staticmethod
    def _prepare_func(
            func: Callable[..., Awaitable[None]],
            **kwargs
    ) -> Awaitable[None]:
        prepared_args: Dict[str, Any] = {
            k: arg for k, arg in kwargs.items()
            if k in getfullargspec(func)[0]
        }

        return func(**prepared_args)
