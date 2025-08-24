from asyncio import Task

from aiogram.fsm.scene import on
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.enums.account_type import AccountType
from app.bot.scenes.base.base_scene import BaseScene
from app.bot.scenes.callback_data import ChangeSceneAction
from app.database.models import Group, Student, Account, Role


class AdminScene(BaseScene, state="admin"):
    @on.message.enter()
    async def on_message_enter(
            self,
            message: Message,
            db: AsyncSession,
    ) -> None:
        await self.send_admin_menu(
            message,
            db
        )

    @on.callback_query.enter()
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            db: AsyncSession
    ) -> None:
        await self.send_admin_menu(
            callback_query.message,
            db
        )

    @on.message()
    async def unknown_message(
            self,
            message: Message
    ) -> None:
        await message.reply(
            _("unknown_message")
        )

    async def send_admin_menu(
            self,
            message: Message,
            db: AsyncSession
    ) -> None:
        groups: Task = await db.scalar(select(func.count()).select_from(Group))
        students: Task = await db.scalar(select(func.count()).select_from(Student))
        parents: Task = await db.scalar(
            select(func.count()).select_from(Account).join(Role).
            filter_by(account_type=AccountType.PARENT.name)
        )

        message_text: str = _("admin.menu").format(
            groups=groups,
            students=students,
            parents=parents
        )

        await message.edit_text(
            message_text,
            reply_markup=self.create_buttons()
        )

    def create_buttons(self):
        builder = InlineKeyboardBuilder()

        with self.i18n.context():
            builder.button(
                text=_("button.stats"),
                callback_data=ChangeSceneAction(to_scene="stats_group").pack()
            )
            builder.button(
                text=_("button.reports"),
                url=str(self.config.reports_url)
            )
            builder.button(
                text=_("button.announcement"),
                callback_data=ChangeSceneAction(to_scene="announcement_group").pack()
            )
            builder.add(self.button_factory.create_back_button())

        builder.adjust(1, True)
        return builder.as_markup()
