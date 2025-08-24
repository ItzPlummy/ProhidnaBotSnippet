from datetime import date
from typing import Any
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from app.bot.classes.calendar import Calendar
from app.bot.scenes.base.calendar_scene import CalendarScene


class StatsCalendarScene(CalendarScene, state="stats_calendar"):
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            calendar: Calendar,
            uuid: UUID | str,
            state: FSMContext,
            update_message: bool = True
    ) -> None:
        await state.update_data(group_id=uuid)

        if update_message:
            await callback_query.message.edit_text(
                _("calendar.choose_date"),
                reply_markup=calendar.as_markup(self.i18n, self.button_factory)
            )

    async def on_calendar_page_turn(
            self,
            callback_query: CallbackQuery,
            calendar: Calendar
    ) -> None:
        await callback_query.message.edit_text(
            _("calendar.choose_date"),
            reply_markup=calendar.as_markup(self.i18n, self.button_factory)
        )

    async def on_day_choice(
            self,
            callback_query: CallbackQuery,
            day: date,
            state: FSMContext
    ) -> None:
        await self.wizard.goto(
            "stats",
            group_id=(await state.get_data())["group_id"],
            add_pagination=False,
            day=day
        )

    async def on_confirm(
            self,
            *args: Any,
            **kwargs: Any
    ) -> None:
        pass

    async def on_back(
            self,
            state: FSMContext
    ) -> None:
        await self.wizard.back(group_id=(await state.get_data())["group_id"])
