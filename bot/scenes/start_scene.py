from typing import Sequence, List, Dict

from aiogram import html
from aiogram.enums import ChatType
from aiogram.fsm.scene import on
from aiogram.types import Message, CallbackQuery, User, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.bot.classes.temp_message_manager import TempMessageManager
from app.bot.enums.account_type import AccountType
from app.bot.scenes.base.base_scene import BaseScene
from app.bot.scenes.callback_data import ChangeSceneAction
from app.database.models import Account, Student


class StartScene(BaseScene, state="start", reset_data_on_enter=True, reset_history_on_enter=True):
    @on.message.enter()
    async def on_message_enter(
            self,
            message: Message,
            db: AsyncSession
    ) -> None:
        if message.chat.type != ChatType.PRIVATE:
            return

        await self.send_menu(
            message,
            message.from_user,
            db,
            reset_message=True
        )

    @on.callback_query.enter()
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            db: AsyncSession,
            temp: TempMessageManager,
            reset_message: bool = False,
            update_message: bool = True
    ) -> None:
        if not update_message:
            return

        await temp.clear(callback_query.message.chat.id)

        await self.send_menu(
            callback_query.message,
            callback_query.from_user,
            db,
            reset_message=reset_message
        )

    @on.message()
    async def unknown_patriotic_message(
            self,
            message: Message
    ) -> None:
        if message.text is not None:
            if message.text.strip().title() in ("Слава Україні!", "Слава Україні"):
                await message.reply(_("patriotic.0"))
                return

            if message.text.strip().title() in ("Слава Нації!", "Слава Нації"):
                await message.reply(_("patriotic.1"))
                return

        await message.reply(
            _("unknown_message")
        )

    async def send_menu(
            self,
            message: Message,
            user: User,
            db: AsyncSession,
            *,
            reset_message: bool = False
    ) -> None:
        account: Account = await db.scalar(
            select(Account).
            filter_by(telegram_id=user.id).
            options(
                joinedload(Account.roles),
                joinedload(Account.group),
                joinedload(Account.students)
            )
        )

        if account is None:
            await self.wizard.goto("contact")
            return

        account_type: AccountType = AccountType.get_main_role(account.roles)

        if account_type is None:
            await self.wizard.goto("contact")
            return

        if account_type == AccountType.SUPERVISOR:
            info: str = account.group.name
        elif account_type == AccountType.PARENT:
            info: str = await self.get_students_as_string(account.students)
        else:
            info: str = ""

        if reset_message:
            await message.answer(
                self.dict_factory.create_start_dict().get(account_type.value).format(info=html.quote(info)),
                reply_markup=self.create_buttons(AccountType.from_sequence(account.roles))
            )
            return

        await message.edit_text(
            self.dict_factory.create_start_dict().get(account_type.value).format(info=html.quote(info)),
            reply_markup=self.create_buttons(AccountType.from_sequence(account.roles))
        )

    def create_buttons(
            self,
            roles: List[AccountType]
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        with self.i18n.context():
            menu_buttons: Dict[AccountType, List[InlineKeyboardButton]] = {
                AccountType.ADMINISTRATOR: [
                    InlineKeyboardButton(
                        text=_("button.admin"),
                        callback_data=ChangeSceneAction(to_scene="admin").pack()
                    )
                ],
                AccountType.MANAGER: [
                    InlineKeyboardButton(
                        text=_("button.stats"),
                        callback_data=ChangeSceneAction(to_scene="stats_group").pack()
                    )
                ],
                AccountType.SUPERVISOR: [
                    InlineKeyboardButton(
                        text=_("button.log"),
                        callback_data=ChangeSceneAction(to_scene="log").pack()
                    )
                ],
                AccountType.PARENT: [
                    InlineKeyboardButton(
                        text=_("button.entries"),
                        callback_data=ChangeSceneAction(to_scene="entries").pack()
                    ),
                    InlineKeyboardButton(
                        text=_("button.notes"),
                        callback_data=ChangeSceneAction(to_scene="send_note_student").pack()
                    )
                ]
            }

            for role in roles:
                for button in menu_buttons[role]:
                    builder.add(button)

            builder.button(
                text=_("button.support"),
                url=str(self.config.support_bot_url)
            )
            builder.button(
                text=_("button.settings"),
                callback_data=ChangeSceneAction(to_scene="settings").pack()
            )

        builder.adjust(1, True)
        return builder.as_markup()

    @staticmethod
    async def get_students_as_string(
            students: Sequence[Student]
    ) -> str:
        student_string: str = ""
        for index, student in enumerate(students):
            student_string += f"{student.full_name}"

            if index == len(students) - 1:
                break
            if index == len(students) - 2:
                student_string += " та "
                continue

            student_string += ", "

        return student_string
