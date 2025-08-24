from typing import List, Dict
from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from app.bot.scenes.base.student_scene import StudentScene


class SendNoteStudentScene(StudentScene, state="send_note_student"):
    async def update(
            self,
            callback_query: CallbackQuery,
            students: List[Dict[str, str]],
            page: int,
            state: FSMContext,
            back: bool = False
    ) -> None:
        if len(students) == 1:
            if back:
                await self.wizard.back()
                return
            student_id: str = str(students[0].get("id"))
            await self.wizard.goto("send_note_calendar", student_id=student_id)
            return

        await callback_query.message.edit_text(
            _("send_note.choose_student"),
            reply_markup=self.create_buttons(
                students,
                page
            )
        )

    async def on_student_choice(
            self,
            callback_query: CallbackQuery,
            student_id: UUID | str
    ) -> None:
        await self.wizard.goto("send_note_calendar", student_id=student_id)
