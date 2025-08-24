from aiogram import F
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.classes.identifier import Identifier
from app.bot.enums.choice import Choice
from app.bot.scenes.base.base_scene import BaseScene
from app.bot.scenes.callback_data import ChoiceAction


class DisableScene(BaseScene, state="disable"):
    @on.callback_query.enter()
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery
    ) -> None:
        await callback_query.message.edit_text(
            _("disable.verify"),
            reply_markup=self.button_factory.create_choice_buttons(as_markup=True)
        )

    @on.callback_query(ChoiceAction.filter(F.choice == Choice.YES))
    async def on_disable(
            self,
            callback_query: CallbackQuery,
            db: AsyncSession,
            identifier: Identifier
    ) -> None:
        await identifier.unidentify(
            callback_query.from_user.id,
            db
        )

        await callback_query.message.edit_text(
            _("disable.disabled")
        )

        await self.wizard.exit()
        await callback_query.answer()

    @on.callback_query(ChoiceAction.filter(F.choice == Choice.NO))
    async def on_not_disable(
            self,
            callback_query: CallbackQuery
    ) -> None:
        await self.wizard.back()
        await callback_query.answer()

    @on.message()
    async def unknown_message(
            self,
            message: Message
    ) -> None:
        await message.reply(
            _("unknown_message")
        )
