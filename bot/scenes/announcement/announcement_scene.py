import asyncio
import logging
from typing import Sequence, Dict, Any

from aiogram import html
from aiogram.exceptions import AiogramError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.classes.temp_message_manager import TempMessageManager
from app.bot.enums.account_type import AccountType
from app.bot.scenes.base.send_scene import SendScene
from app.bot.scenes.callback_data import SendAction
from app.database.models import Group, Student, Account, Role, StudentsParents


class AnnouncementScene(SendScene, state="announcement"):
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            group_id: str,
            db: AsyncSession,
            state: FSMContext
    ) -> None:
        if group_id is None:
            group_info: str = _("announcement.all_groups")
        else:
            group: Group | None = (
                await db.scalar(
                    select(Group)
                    .filter_by(id=group_id)
                )
            )

            group_info: str = group.name

        await asyncio.create_task(state.update_data(group_id=group_id, info=group_info))

        await callback_query.message.edit_text(
            _("announcement.blank").format(info=html.quote(group_info)),
            reply_markup=self.button_factory.create_back_button(as_markup=True)
        )

    async def on_message(
            self,
            message: Message,
            message_id: int,
            text: str,
            data: Dict[str, Any]
    ) -> None:
        group_info: str | None = data.get("info")

        if group_info is None:
            return

        await message.bot.edit_message_text(
            _("announcement.with_message").format(
                info=html.quote(group_info),
                message=html.quote(text)
            ),
            chat_id=message.from_user.id,
            message_id=message_id,
            reply_markup=self.create_buttons()
        )

    async def on_send(
            self,
            callback_query: CallbackQuery,
            message_id: int,
            text: str,
            db: AsyncSession,
            data: Dict[str, Any],
            temp: TempMessageManager
    ) -> None:
        group_id: str | None = data.get("group_id")

        if group_id:
            parents: Sequence[Account] = (
                await db.execute(
                    select(Account).
                    filter(Account.telegram_id.is_not(None)).
                    join(Role).
                    filter_by(account_type=AccountType.PARENT.name).
                    join(StudentsParents).
                    join(Student).
                    filter_by(group_id=group_id)
                )
            ).unique().scalars().all()
        else:
            parents: Sequence[Account] = (
                await db.execute(
                    select(Account).
                    filter(Account.telegram_id.is_not(None)).
                    join(Role).
                    filter_by(account_type=AccountType.PARENT.name)
                )
            ).unique().scalars().all()

        await callback_query.answer()
        sending_message = await callback_query.message.answer(_("announcement.is_sending").format(parents=len(parents)))

        successful_sends: int = 0
        for parent in parents:
            try:
                await callback_query.bot.send_message(chat_id=parent.telegram_id,text=text)
                successful_sends += 1
            except AiogramError as e:
                logging.error(e)
                continue
            await asyncio.sleep(0.1)

        await callback_query.message.answer(
            _("announcement.sent").format(successful_sends=successful_sends, parents=len(parents)),
            reply_markup=self.button_factory.create_menu_button(as_markup=True)
        )

        await temp.add(sending_message.chat.id, message_id)
        await temp.add(sending_message.chat.id, sending_message.message_id)

    def create_buttons(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        with self.i18n.context():
            builder.button(
                text=_("button.send_announcement"),
                callback_data=SendAction().pack()
            )
            builder.add(self.button_factory.create_back_button())

        builder.adjust(1, True)
        return builder.as_markup()
