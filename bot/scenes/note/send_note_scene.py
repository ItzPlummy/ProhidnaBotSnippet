import asyncio
from datetime import date
from typing import List, Dict, Any
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.classes.calendar import Calendar
from app.bot.classes.temp_message_manager import TempMessageManager
from app.bot.enums.account_type import AccountType
from app.bot.scenes.base.send_scene import SendScene
from app.bot.scenes.callback_data import SendAction
from app.database.models import Account, Student, Role, Group, Excuse
from app.statistics.enums.excuse_type import ExcuseType


class SendNoteScene(SendScene, state="send_note"):
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            state: FSMContext,
            student_id: UUID | str,
            selected_days: List[date]
    ) -> None:
        await asyncio.create_task(
            state.update_data(
                student_id=str(student_id),
                days=Calendar.serialize_days(selected_days)
            )
        )

        await callback_query.message.edit_text(
            _("send_note.blank"),
            reply_markup=self.button_factory.create_back_button(as_markup=True)
        )

    async def on_message(
            self,
            message: Message,
            message_id: int,
            text: str,
            data: Dict[str, Any]
    ) -> None:
        if "student_id" not in data:
            return

        await message.bot.edit_message_text(
            _("send_note.with_message").format(
                text=text,
            ),
            chat_id=message.chat.id,
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
        student_id: str = data.get("student_id")

        if student_id is None:
            return

        selected_days: List[date] = Calendar.deserialize_days(data.get("days"))

        for selected_day in selected_days:
            excuse: Excuse = Excuse(
                student_id=student_id,
                date=selected_day,
                excuse_type=ExcuseType.ESTEEMED_REASON.name,
                description=text
            )
            db.add(excuse)
        await db.commit()

        parent_full_name: str = await db.scalar(
            select(Account.full_name)
            .filter_by(telegram_id=callback_query.from_user.id)
            .join(Role)
            .filter_by(account_type=AccountType.PARENT.name)
        )

        student_full_name: str = await db.scalar(
            select(Student.full_name)
            .filter_by(id=student_id)
        )

        supervisor_telegram_id: int = await db.scalar(
            select(Account.telegram_id)
            .join(Role)
            .filter_by(account_type=AccountType.SUPERVISOR.name)
            .join(Group)
            .join(Student)
            .filter_by(id=student_id)
        )

        if supervisor_telegram_id is not None:
            await callback_query.bot.send_message(
                supervisor_telegram_id,
                _("send_note.received").format(
                    text=text,
                    parent_full_name=parent_full_name,
                    student_full_name=student_full_name,
                    dates="\n".join(Calendar.serialize_days(selected_days, "%d.%m.%y"))
                )
            )

        await callback_query.answer()

        await callback_query.message.answer(
            _("sent_note.sent"),
            reply_markup=self.button_factory.create_menu_button(as_markup=True)
        )

        await temp.add(callback_query.message.chat.id, message_id)

    async def on_back(
            self,
            state: FSMContext
    ) -> None:
        data: Dict[str, Any] = await state.get_data()
        await self.wizard.back(
            student_id=data.get("student_id"),
            selected_days=data.get("selected_days"),
            text=data.get("text")
        )

    def create_buttons(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        with self.i18n.context():
            builder.button(
                text=_("button.send_note"),
                callback_data=SendAction().pack()
            )
            builder.add(self.button_factory.create_back_button())

        builder.adjust(1, True)
        return builder.as_markup()
