import asyncio
from abc import abstractmethod, ABC
from datetime import date
from typing import List, Any, Dict
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.scenes.base.page_scene import PageScene
from app.bot.scenes.callback_data import CalendarChoiceAction
from app.statistics.models.page_model import PageModel
from app.statistics.page_creator import PageCreator


class PageLogScene(PageScene, ABC):
    def __init__(
            self,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.creator: PageCreator | None = None

    @abstractmethod
    async def on_callback_query_enter(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    async def update(
            self,
            callback_query: CallbackQuery,
            page: int,
            add_pagination: bool,
            state: FSMContext
    ) -> None: pass

    @abstractmethod
    async def on_calendar_choice(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    async def create_data(
            self,
            uuid: UUID | str,
            date_range: List[date]
    ) -> Any: pass

    @abstractmethod
    async def create_date_range(
            self,
            uuid: UUID | str,
            limit: int,
            previous_date: date | None = None,
    ) -> List[date]: pass

    @on.callback_query.enter()
    async def __on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            state: FSMContext,
            page: int = 0,
            add_pagination: bool = True,
            day: date | None = None,
            **kwargs
    ) -> None:
        await state.update_data(add_pagination=add_pagination)

        await self._prepare_func(
            self.on_callback_query_enter,
            callback_query=callback_query,
            state=state,
            **kwargs
        )

        if day is not None:
            await state.update_data(
                year=day.year,
                month=day.month
            )

            uuid: UUID | str = (await state.get_data())["uuid"]
            page = await self.__get_page_by_date(uuid, day)

            if page is None:
                await callback_query.answer(_("answer.no_logs_at_date"), show_alert=False)
                await self.wizard.back(
                    uuid=uuid,
                    year=day.year,
                    month=day.month,
                    update_message=False
                )
                return

        await self.update(
            callback_query,
            page,
            add_pagination,
            state
        )

    @on.message()
    async def unknown_message(
            self,
            message: Message
    ) -> None:
        await message.reply(
            _("unknown_message")
        )

    @on.callback_query(CalendarChoiceAction.filter())
    async def __on_date_choice(
            self,
            callback_query: CallbackQuery,
            **kwargs
    ) -> None:
        await self._prepare_func(
            self.on_calendar_choice,
            callback_query=callback_query,
            **kwargs
        )

    async def on_page_turn(
            self,
            callback_query: CallbackQuery,
            page: int,
            state: FSMContext
    ) -> None:
        add_pagination: bool = (await state.get_data())["add_pagination"]

        await self.update(
            callback_query,
            page,
            add_pagination,
            state
        )

    async def on_back(
            self,
            state: FSMContext
    ) -> None:
        data: Dict[str, Any] = await state.get_data()

        await self.wizard.back(
            uuid=data.get("uuid"),
            year=data.get("year"),
            month=data.get("month")
        )

    async def get_page(
            self,
            callback_query: CallbackQuery,
            page: int,
            state: FSMContext
    ) -> PageModel | None:
        data: Dict[str, Any] = await state.get_data()
        uuid: UUID | str = data.get("uuid")
        date_range: List[date] = self.date_manager.get_from_data(data.get("date_range"))

        if page < 0:
            await callback_query.answer(_("answer.no_page"), show_alert=False)
            return

        previous_page: int = data.get("page")
        if previous_page is None:
            previous_page = -1
        await state.update_data(page=page)

        partition: int = page // self.config.date_partition_size
        previous_partition: int = previous_page // self.config.date_partition_size

        if partition != previous_partition:
            date_range: List[date] = await self.__create_date_range(
                uuid,
                page,
                self.config.date_partition_size,
                date_range
            )

            if not date_range:
                await callback_query.answer(_("answer.no_logs"), show_alert=False)
                await self.wizard.back(update_message=False)
                return

            if page >= len(date_range):
                await callback_query.answer(_("answer.no_page"), show_alert=False)
                return

            range_start: int = partition * self.config.date_partition_size
            range_end: int = (partition + 1) * self.config.date_partition_size

            page_data: Any = await self.create_data(uuid, date_range[range_start:range_end])

            await asyncio.create_task(self.date_manager.update(date_range, state))
            await asyncio.create_task(state.update_data(page_data=page_data))
        else:
            if page >= len(date_range):
                await callback_query.answer(_("answer.no_page"), show_alert=False)
                return

            page_data: Any = data.get("page_data")

        return self.creator.create(
            self.creator.deserialize(page_data[page % self.config.date_partition_size]),
            date_range[page],
            page
        )

    def create_buttons(
            self,
            page: int = 0,
            *,
            add_pagination: bool = False
    ) -> InlineKeyboardMarkup:
        builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

        if add_pagination:
            builder.row(self.button_factory.create_date_choice_button())
            builder.row(*self.button_factory.create_pagination_buttons(page))
            builder.add(self.button_factory.create_back_button())
            builder.adjust(1, 2, 1)
        else:
            builder.add(self.button_factory.create_back_button())

        return builder.as_markup()

    async def __create_date_range(
            self,
            uuid: UUID | str,
            page: int,
            date_partition_size: int,
            date_range: List[date] | None
    ) -> List[date]:
        if date_range is None:
            date_range = await self.create_date_range(uuid, date_partition_size)
            if not date_range:
                return date_range

        while len(date_range) <= page:
            new_date_partition: List[date] = await self.create_date_range(uuid, date_partition_size, date_range[-1])
            date_range.extend(new_date_partition)

        return date_range

    async def __get_page_by_date(
            self,
            uuid: UUID | str,
            day: date
    ) -> int | None:
        page: int = 0
        date_range: List[date] = []

        while True:
            date_range = await self.__create_date_range(
                uuid,
                page,
                self.config.date_partition_size,
                date_range if date_range else None
            )
            page += self.config.date_partition_size

            if day in date_range:
                break

            if page > len(date_range) or date_range[-1] < day:
                return

        return date_range.index(day)
