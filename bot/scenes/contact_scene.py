from typing import List
from uuid import UUID

from aiogram import F
from aiogram.fsm.scene import on
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.payload import decode_payload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.classes.identifier import Identifier
from app.bot.classes.temp_message_manager import TempMessageManager
from app.bot.enums.account_type import AccountType
from app.bot.scenes.base.base_scene import BaseScene
from app.bot.scenes.callback_data import TryAgainAction
from app.database.models import Account


class ContactScene(BaseScene, state="contact"):
    @on.message.enter()
    async def on_message_enter(
            self,
            message: Message,
            db: AsyncSession,
            temp: TempMessageManager,
            identifier: Identifier
    ) -> None:
        account_type: AccountType | None = await self.payload_identify(
            identifier,
            message.text,
            message.from_user.id,
            db
        )

        if account_type is not None:
            await self.send_verification_message(
                message,
                account_type
            )
        else:
            await self.send_contact_message(
                message,
                temp
            )

    @on.message(F.contact)
    async def on_contact(
            self,
            message: Message,
            db: AsyncSession,
            temp: TempMessageManager,
            identifier: Identifier
    ) -> None:
        await temp.add(message.chat.id, message.message_id)

        if message.contact.user_id != message.from_user.id:
            new_message: Message = await message.reply(
                _("contact.unknown_contact"),
                reply_markup=self.button_factory.create_try_again_button(as_markup=True)
            )
            await temp.add(new_message.chat.id, new_message.message_id)

            return

        phone_number: str = message.contact.phone_number.replace('+', '')

        account_id: UUID = await db.scalar(
            select(Account.id).
            filter_by(phone_number=phone_number)
        )

        if account_id is None:
            new_message: Message = await message.reply(
                _("contact.unknown_contact"),
                reply_markup=self.button_factory.create_try_again_button(as_markup=True)
            )
            await temp.add(new_message.chat.id, new_message.message_id)

            return

        account_type: AccountType = await identifier.identify(
            account_id,
            message.from_user.id,
            db
        )

        await self.send_verification_message(
            message,
            account_type
        )

        await temp.clear(message.chat.id)

    @on.callback_query(TryAgainAction.filter())
    async def on_try_again(
            self,
            callback_query: CallbackQuery,
            temp: TempMessageManager
    ):
        await temp.clear(callback_query.from_user.id)

        await self.send_contact_message(
            callback_query.message,
            temp
        )

    @on.message()
    async def unknown_message(
            self,
            message: Message,
            temp: TempMessageManager
    ) -> None:
        await temp.add(message.chat.id, message.message_id)

        new_message: Message = await message.reply(
            _("unknown_message"),
            reply_markup=self.button_factory.create_contact_button(as_markup=True)
        )
        await temp.add(new_message.chat.id, new_message.message_id)

    async def send_contact_message(
            self,
            message: Message,
            temp: TempMessageManager
    ) -> None:
        new_message: Message = await message.answer(
            _("menu.start").format(send_contact=_("button.send_contact")),
            reply_markup=self.button_factory.create_contact_button(as_markup=True)
        )
        await temp.add(new_message.chat.id, new_message.message_id)

    async def send_verification_message(
            self,
            message: Message,
            account_type: AccountType
    ) -> None:
        await message.answer(
            self.dict_factory.create_verification_dict().get(account_type.value),
            reply_markup=self.button_factory.create_menu_button(go_to=True, as_markup=True)
        )

    @staticmethod
    async def payload_identify(
            identifier: Identifier,
            message_text: str,
            user_id: int,
            db: AsyncSession
    ) -> AccountType | None:
        if message_text is None:
            return None

        args: List[str] = message_text.split()

        if len(args) <= 1:
            return

        encoded_payload: str = args[1]
        payload: str | None = None

        try:
            payload = decode_payload(encoded_payload)
        except UnicodeDecodeError:
            pass

        if not payload:
            return

        return await identifier.identify(
            payload,
            user_id,
            db
        )
