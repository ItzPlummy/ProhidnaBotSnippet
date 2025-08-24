from datetime import date
from typing import List, Any
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.scenes.base.page_log_scene import PageLogScene
from app.database.models import Account, Group
from app.statistics.models.page_logs_model import PageLogsModel


class LogScene(PageLogScene, state="log"):
    def __init__(
            self,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.creator = self.logs_creator

    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            db: AsyncSession,
            state: FSMContext
    ) -> None:
        group_id: UUID = await db.scalar(
            select(Group.id)
            .join(Account)
            .filter_by(telegram_id=callback_query.from_user.id)
        )

        await state.update_data(uuid=str(group_id))

    async def update(
            self,
            callback_query: CallbackQuery,
            page: int,
            add_pagination: bool,
            state: FSMContext
    ) -> None:
        logs: PageLogsModel | None = await self.get_page(
            callback_query,
            page,
            state
        )

        if logs is None:
            return

        await callback_query.message.edit_text(
            logs.as_message(self.dict_factory, state="log"),
            reply_markup=self.create_buttons(page, add_pagination=add_pagination)
        )

    async def on_calendar_choice(self) -> None:
        await self.wizard.goto("log_calendar")

    async def create_data(
            self,
            group_id: UUID | str,
            date_range: List[date]
    ) -> Any:
        return await self.creator.create_serializable(
            group_id,
            date_range,
            self.start_time
        )

    async def create_date_range(
            self,
            group_id: UUID | str,
            limit: int,
            previous_date: date | None = None
    ) -> List[date]:
        return await self.creator.data_creator.create_logs_date_range(
            group_id,
            limit,
            previous_date
        )
