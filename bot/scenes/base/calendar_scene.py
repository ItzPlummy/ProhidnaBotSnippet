import asyncio
from abc import abstractmethod, ABC
from copy import copy
from datetime import date, datetime
from typing import Any, List

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from pytz import utc

from app.bot.classes.calendar import Calendar
from app.bot.scenes.base.page_scene import PageScene
from app.bot.scenes.callback_data import CalendarDayChoiceAction, CalendarConfirmAction


class CalendarScene(PageScene, ABC):
    @abstractmethod
    async def on_callback_query_enter(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    async def on_calendar_page_turn(
            self,
            *args: Any,
            **kwargs: Any
    ) -> None: pass

    @abstractmethod
    async def on_day_choice(
            self,
            *args: Any,
            **kwargs: Any
    ) -> None: pass

    @abstractmethod
    async def on_confirm(
            self,
            *args: Any,
            **kwargs: Any
    ) -> None: pass

    @on.callback_query.enter()
    async def __on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            state: FSMContext,
            year: int | None = None,
            month: int | None = None,
            selected_days: List[str] | None = None,
            **kwargs
    ) -> None:
        calendar: Calendar = Calendar(
            year=year,
            month=month,
            selected_days=Calendar.deserialize_days(selected_days) if selected_days is not None else None
        )

        await self._prepare_func(
            self.on_callback_query_enter,
            callback_query=callback_query,
            calendar=calendar,
            state=state,
            **kwargs
        )

        await asyncio.create_task(calendar.to_state(state))

    @on.callback_query(CalendarDayChoiceAction.filter())
    async def __on_day_choice(
            self,
            callback_query: CallbackQuery,
            callback_data: CalendarDayChoiceAction,
            state: FSMContext,
            **kwargs: Any
    ) -> None:
        calendar: Calendar = await Calendar.from_state(state)

        day: int = callback_data.day
        if not day:
            await callback_query.answer()
            return

        year: int = callback_data.year
        month: int = callback_data.month

        await self._prepare_func(
            self.on_day_choice,
            callback_query=callback_query,
            calendar=calendar,
            day=date(year, month, day),
            state=state,
            **kwargs
        )

        await asyncio.create_task(calendar.to_state(state))

    @on.callback_query(CalendarConfirmAction.filter())
    async def __on_confirm(
            self,
            callback_query: CallbackQuery,
            state: FSMContext,
            **kwargs
    ) -> None:
        calendar: Calendar = await Calendar.from_state(state)

        if not calendar.selected_days:
            await callback_query.answer(_("answer.not_enough_days"))
            return

        await self._prepare_func(
            self.on_confirm,
            callback_query=callback_query,
            calendar=calendar,
            selected_days=calendar.selected_days,
            state=state,
            **kwargs
        )

        await asyncio.create_task(calendar.to_state(state))

    async def on_page_turn(
            self,
            callback_query: CallbackQuery,
            page: int,
            state: FSMContext,
            **kwargs
    ) -> None:
        calendar: Calendar = await Calendar.from_state(state)
        if calendar is None:
            return

        now: date = datetime.now(utc).date()
        next_calendar: Calendar = copy(calendar)
        next_calendar.add(-page)
        if now.year == next_calendar.year and now.month == next_calendar.month and page > 0:
            await callback_query.answer(_("answer.no_page"), show_alert=False)
            return

        calendar.add(page)

        await self._prepare_func(
            self.on_calendar_page_turn,
            callback_query=callback_query,
            calendar=calendar,
            state=state,
            **kwargs
        )

        await asyncio.create_task(calendar.to_state(state))
