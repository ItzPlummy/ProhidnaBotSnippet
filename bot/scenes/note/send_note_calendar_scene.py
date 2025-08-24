import asyncio
from datetime import date
from typing import Any, Dict, List
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from app.bot.classes.calendar import Calendar
from app.bot.scenes.base.calendar_scene import CalendarScene


class SendNoteCalendarScene(CalendarScene, state="send_note_calendar"):
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            calendar: Calendar,
            state: FSMContext,
            student_id: UUID | str
    ) -> None:
        await callback_query.message.edit_text(
            _("notes.choose_days"),
            reply_markup=calendar.as_markup(self.i18n, self.button_factory, with_confirm=True)
        )

        await asyncio.create_task(state.update_data(student_id=student_id))

    async def on_calendar_page_turn(
            self,
            callback_query: CallbackQuery,
            calendar: Calendar
    ) -> None:
        await callback_query.message.edit_text(
            _("notes.choose_days"),
            reply_markup=calendar.as_markup(self.i18n, self.button_factory, with_confirm=True)
        )

    async def on_day_choice(
            self,
            callback_query: CallbackQuery,
            calendar: Calendar,
            day: date
    ) -> None:
        selected: bool = calendar.select(day)

        if not selected:
            await callback_query.answer(_("answer.too_many_days"), show_alert=False)

        await callback_query.message.edit_text(
            _("notes.choose_days"),
            reply_markup=calendar.as_markup(self.i18n, self.button_factory, with_confirm=True)
        )

    async def on_confirm(
            self,
            selected_days: List[date],
            state: FSMContext
    ) -> None:
        data: Dict[str, Any] = await state.get_data()

        await self.wizard.goto(
            "send_note",
            student_id=data.get("student_id"),
            selected_days=selected_days
        )

    async def on_back(self) -> None:
        await self.wizard.back(back=True)
