from typing import Tuple

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _, I18n

from app.bot.scenes.callback_data import (
    ChoiceAction,
    PageAction,
    BackAction,
    MenuAction,
    TryAgainAction, CalendarChoiceAction
)


class ButtonFactory:
    def __init__(
            self,
            i18n: I18n
    ) -> None:
        self.i18n: I18n = i18n

    def create_pagination_buttons(
            self,
            page: int = 0,
            *,
            as_markup: bool = False
    ) -> InlineKeyboardMarkup | Tuple[InlineKeyboardButton, InlineKeyboardButton]:
        with self.i18n.context():
            buttons: Tuple[InlineKeyboardButton, InlineKeyboardButton] = (
                InlineKeyboardButton(
                    text=_("button.left"),
                    callback_data=PageAction(page=page - 1).pack()
                ),
                InlineKeyboardButton(
                    text=_("button.right"),
                    callback_data=PageAction(page=page + 1).pack()
                )
            )

        if as_markup:
            return InlineKeyboardMarkup(inline_keyboard=[[*buttons]])
        return buttons

    def create_choice_buttons(
            self,
            *,
            as_markup: bool = False
    ) -> InlineKeyboardMarkup | Tuple[InlineKeyboardButton, InlineKeyboardButton]:
        with self.i18n.context():
            buttons: Tuple[InlineKeyboardButton, InlineKeyboardButton] = (
                InlineKeyboardButton(
                    text=_("button.yes"),
                    callback_data=ChoiceAction(choice=True).pack()
                ),
                InlineKeyboardButton(
                    text=_("button.no"),
                    callback_data=ChoiceAction(choice=False).pack()
                )
            )

        if as_markup:
            return InlineKeyboardMarkup(inline_keyboard=[[*buttons]])
        return buttons

    def create_date_choice_button(
            self,
            *,
            as_markup: bool = False
    ) -> InlineKeyboardMarkup | InlineKeyboardButton:
        with self.i18n.context():
            button: InlineKeyboardButton = InlineKeyboardButton(
                text=_("button.choose_date"),
                callback_data=CalendarChoiceAction().pack()
            )

        if as_markup:
            return InlineKeyboardMarkup(inline_keyboard=[[button]])
        return button

    def create_menu_button(
            self,
            go_to: bool = False,
            *,
            as_markup: bool = False
    ) -> InlineKeyboardMarkup | InlineKeyboardButton:
        with self.i18n.context():
            if go_to:
                message_tag: str = _("button.go_to_menu")
            else:
                message_tag: str = _("button.menu")

            button: InlineKeyboardButton = InlineKeyboardButton(
                text=message_tag,
                callback_data=MenuAction().pack()
            )

        if as_markup:
            return InlineKeyboardMarkup(inline_keyboard=[[button]])
        return button

    def create_contact_button(
            self,
            *,
            as_markup: bool = False
    ) -> ReplyKeyboardMarkup | KeyboardButton:
        with self.i18n.context():
            button: KeyboardButton = KeyboardButton(
                text=_("button.send_contact"),
                request_contact=True
            )

        if as_markup:
            return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
        return button

    def create_try_again_button(
            self,
            *,
            as_markup: bool = False
    ) -> InlineKeyboardMarkup | InlineKeyboardButton:
        with self.i18n.context():
            button: InlineKeyboardButton = InlineKeyboardButton(
                text=_("button.try_again"),
                callback_data=TryAgainAction().pack()
            )

        if as_markup:
            return InlineKeyboardMarkup(inline_keyboard=[[button]])
        return button

    def create_back_button(
            self,
            *,
            as_markup: bool = False
    ) -> InlineKeyboardMarkup | InlineKeyboardButton:
        with self.i18n.context():
            button: InlineKeyboardButton = InlineKeyboardButton(
                text=_("button.back"),
                callback_data=BackAction().pack()
            )

        if as_markup:
            return InlineKeyboardMarkup(inline_keyboard=[[button]])
        return button
