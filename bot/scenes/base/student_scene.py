import asyncio
from abc import abstractmethod
from typing import List, Dict
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.enums.account_type import AccountType
from app.bot.scenes.base.page_scene import PageScene
from app.bot.scenes.callback_data import StudentChoiceAction
from app.database.models import Student, Account, Role


class StudentScene(PageScene):
    @abstractmethod
    async def update(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    async def on_student_choice(
            self,
            *args,
            **kwargs
    ) -> None: pass

    async def on_page_turn(
            self,
            callback_query: CallbackQuery,
            page: int,
            state: FSMContext,
            **kwargs
    ) -> None:
        if page < 0:
            await callback_query.answer(_("answer.no_page"), show_alert=False)
            return

        students: List[List[Dict[str, str]]] = (await state.get_data())["students"]

        if page >= len(students):
            await callback_query.answer(_("answer.no_page"), show_alert=False)
            return

        await self._prepare_func(
            self.update,
            callback_query=callback_query,
            students=students[page],
            page=page,
            state=state,
            **kwargs
        )

    @on.callback_query.enter()
    async def __on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            db: AsyncSession,
            state: FSMContext,
            **kwargs
    ) -> None:
        parent_id: UUID = await db.scalar(
            select(Account.id)
            .filter_by(telegram_id=callback_query.from_user.id)
            .join(Role)
            .filter_by(account_type=AccountType.PARENT.name)
        )

        students: List[List[Student]] = await self.data_creator.get_students(parent_id=parent_id)
        if not students:
            await self.wizard.back(update_message=False)
            return

        serialized_students: List[List[Dict[str, str]]] = self.serialize_students(students)

        await self._prepare_func(
            self.update,
            callback_query=callback_query,
            students=serialized_students[0],
            page=0,
            state=state,
            **kwargs
        )

        await asyncio.create_task(state.update_data(students=serialized_students))

    @on.callback_query(StudentChoiceAction.filter())
    async def __on_student_choice(
            self,
            callback_query: CallbackQuery,
            callback_data: StudentChoiceAction,
            **kwargs
    ) -> None:
        await self._prepare_func(
            self.on_student_choice,
            callback_query=callback_query,
            student_id=callback_data.student_id,
            **kwargs
        )

    def create_buttons(
            self,
            students: List[Dict[str, str]],
            page: int
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        with self.i18n.context():
            for student in students:
                builder.button(
                    text=_("button.student").format(full_name=student["full_name"]),
                    callback_data=StudentChoiceAction(student_id=student["id"]).pack()
                )

            builder.add(*self.button_factory.create_pagination_buttons(page))
            builder.add(self.button_factory.create_back_button())

        builder.adjust(*([1] * len(students)), 2, 1)
        return builder.as_markup()

    @staticmethod
    def serialize_students(students: List[List[Student]]) -> List[List[Dict[str, str]]]:
        return [
            [
                {"id": str(student.id), "full_name": student.full_name}
                for student in students_partition
            ]
            for students_partition in students
        ]
