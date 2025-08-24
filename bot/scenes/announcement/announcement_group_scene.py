from typing import List, Dict

from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from app.bot.scenes.base.group_scene import GroupScene


class AnnouncementGroupScene(GroupScene, state="announcement_group"):
    async def update(
            self,
            callback_query: CallbackQuery,
            groups: List[Dict[str, str]],
            page: int
    ) -> None:
        await callback_query.message.edit_text(
            _("announcement.choose_group"),
            reply_markup=self.create_buttons(
                groups,
                page,
                all_groups=True
            )
        )

    async def on_group_choice(
            self,
            group_id: str
    ) -> None:
        await self.wizard.goto("announcement", group_id=group_id)
