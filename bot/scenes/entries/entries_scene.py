from datetime import date
from typing import List, Any
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.scenes.base.page_log_scene import PageLogScene
from app.database.models import Account
from app.statistics.models.page_entries_model import PageEntriesModel


class EntriesScene(PageLogScene, state="entries"):
    def __init__(
            self,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.creator = self.entries_creator

    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            db: AsyncSession,
            state: FSMContext
    ) -> None:
        parent_id: UUID = await db.scalar(
            select(Account.id)
            .filter_by(telegram_id=callback_query.from_user.id)
        )

        await state.update_data(uuid=str(parent_id))

    async def update(
            self,
            callback_query: CallbackQuery,
            page: int,
            add_pagination: bool,
            state: FSMContext
    ) -> None:
        entries: PageEntriesModel | None = await self.get_page(
            callback_query,
            page,
            state
        )

        if entries is None:
            return

        await callback_query.message.edit_text(
            entries.as_message(self.dict_factory),
            reply_markup=self.create_buttons(page, add_pagination=add_pagination)
        )

    async def on_calendar_choice(self) -> None:
        await self.wizard.goto("entries_calendar")

    async def create_data(
            self,
            parent_id: UUID | str,
            date_range: List[date]
    ) -> Any:
        return await self.creator.create_serializable(
            parent_id,
            date_range
        )

    async def create_date_range(
            self,
            parent_id: UUID | str,
            limit: int,
            previous_date: date | None = None
    ) -> List[date]:
        return await self.creator.data_creator.create_entries_date_range(
            parent_id,
            limit,
            previous_date
        )
