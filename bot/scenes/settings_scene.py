from typing import Dict
from uuid import UUID

from aiogram.fsm.scene import on
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, update, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.enums.setting import BoolSetting
from app.bot.scenes.base.base_scene import BaseScene
from app.bot.scenes.callback_data import ChangeSettingAction, ChangeBoolSettingAction, ChangeSceneAction
from app.database.models import Settings, Account


class SettingsScene(BaseScene, state="settings"):
    @on.callback_query.enter()
    async def on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            db: AsyncSession
    ) -> None:
        account_id: UUID = await db.scalar(
            select(Account.id).
            filter_by(telegram_id=callback_query.from_user.id)
        )

        if not await db.scalar(exists().where(Settings.account_id == account_id).select()):
            settings = Settings(account_id=account_id)
            db.add(settings)
            await db.commit()
        else:
            settings: Settings = await db.scalar(
                select(Settings).
                filter_by(account_id=account_id)
            )

        await callback_query.message.edit_text(
            _("settings.menu"),
            reply_markup=self.create_buttons(settings)
        )

    @on.callback_query(ChangeBoolSettingAction.filter())
    async def change_bool_setting(
            self,
            callback_query: CallbackQuery,
            callback_data: ChangeSettingAction,
            db: AsyncSession
    ):
        account_id: UUID = await db.scalar(
            select(Account.id).
            filter_by(telegram_id=callback_query.from_user.id)
        )

        await db.execute(
            update(Settings).
            filter_by(account_id=account_id).
            values(**{callback_data.setting.value: callback_data.value})
        )

        await db.commit()

        await callback_query.answer(
            self.dict_factory.create_settings_answer_dict().get(callback_data.setting).get(callback_data.value),
            show_alert=False,
        )

        await self.wizard.enter()

    @on.message()
    async def unknown_message(
            self,
            message: Message
    ) -> None:
        await message.reply(
            _("unknown_message")
        )

    def create_buttons(
            self,
            settings: Settings
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        button_dict: Dict[BoolSetting, Dict[bool, str]] = self.dict_factory.create_settings_button_dict()

        with self.i18n.context():
            builder.button(
                text=button_dict.get(BoolSetting.ALLOW_MESSAGES).get(settings.send_bot_messages),
                callback_data=ChangeBoolSettingAction(
                    setting=BoolSetting.ALLOW_MESSAGES,
                    value=not settings.send_bot_messages
                ).pack()
            )

            if settings.send_bot_messages:
                builder.button(
                    text=button_dict.get(BoolSetting.ALLOW_VARIATIONS).get(settings.allow_bot_variations),
                    callback_data=ChangeBoolSettingAction(
                        setting=BoolSetting.ALLOW_VARIATIONS,
                        value=not settings.allow_bot_variations
                    ).pack()
                )

            builder.button(
                text=_("button.disable_bot"),
                callback_data=ChangeSceneAction(to_scene="disable").pack()
            )
            builder.add(self.button_factory.create_back_button())

        builder.adjust(1, True)
        return builder.as_markup()
