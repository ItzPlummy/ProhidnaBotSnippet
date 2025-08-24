from typing import List, Dict

from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from app.bot.scenes.base.group_scene import GroupScene


class StatsGroupScene(GroupScene, state="stats_group"):
    async def update(
            self,
            callback_query: CallbackQuery,
            groups: List[Dict[str, str]],
            page: int
    ) -> None:
        await callback_query.message.edit_text(
            _("stats.choose_group"),
            reply_markup=self.create_buttons(
                groups,
                page,
                all_groups=False
            )
        )

    async def on_group_choice(
            self,
            group_id: str
    ) -> None:
        await self.wizard.goto("stats", group_id=group_id)
