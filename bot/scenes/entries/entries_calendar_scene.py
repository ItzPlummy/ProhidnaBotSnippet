from datetime import date
from typing import Any
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.classes.calendar import Calendar
from app.bot.scenes.base.calendar_scene import CalendarScene
from app.database.models import Account


class EntriesCalendarScene(CalendarScene, state="entries_calendar"):
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            calendar: Calendar,
            db: AsyncSession,
            state: FSMContext,
            update_message: bool = True
    ) -> None:
        parent_id: UUID = await db.scalar(
            select(Account.id)
            .filter_by(telegram_id=callback_query.from_user.id)
        )

        await state.update_data(uuid=str(parent_id))

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
            day: date,
    ) -> None:
        await self.wizard.goto(
            "entries",
            add_pagination=False,
            day=day
        )

    async def on_confirm(
            self,
            *args: Any,
            **kwargs: Any
    ) -> None:
        pass
