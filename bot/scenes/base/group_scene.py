import asyncio
from abc import abstractmethod
from typing import List, Dict

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.scenes.base.page_scene import PageScene
from app.bot.scenes.callback_data import GroupChoiceAction
from app.database.models import Group


class GroupScene(PageScene):
    @abstractmethod
    async def update(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    async def on_group_choice(
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

        groups: List[List[Dict[str, str]]] = (await state.get_data())["groups"]

        if page >= len(groups):
            await callback_query.answer(_("answer.no_page"), show_alert=False)
            return

        await self._prepare_func(
            self.update,
            callback_query=callback_query,
            groups=groups[page],
            page=page,
            state=state,
            **kwargs
        )

    @on.callback_query.enter()
    async def __on_callback_query_enter(
            self,
            callback_query: CallbackQuery,
            state: FSMContext,
            **kwargs
    ) -> None:
        groups: List[List[Dict[str, str]]] = self.serialize_groups(await self.data_creator.get_groups())
        await asyncio.create_task(state.update_data(groups=groups))

        await self._prepare_func(
            self.update,
            callback_query=callback_query,
            groups=groups[0],
            page=0,
            state=state,
            **kwargs
        )

    @on.callback_query(GroupChoiceAction.filter())
    async def __on_group_choice(
            self,
            callback_query: CallbackQuery,
            callback_data: GroupChoiceAction,
            **kwargs
    ) -> None:
        await self._prepare_func(
            self.on_group_choice,
            callback_query=callback_query,
            group_id=callback_data.group_id,
            **kwargs
        )

    @staticmethod
    def serialize_groups(groups: List[List[Group]]) -> List[List[Dict[str, str]]]:
        return [
            [
                {"id": str(group.id), "name": group.name, "full_name": group.supervisor.full_name}
                if group.supervisor is not None else
                {"id": str(group.id), "name": group.name}
                for group in parallel
            ]
            for parallel in groups
        ]

    def create_buttons(
            self,
            groups: List[Dict[str, str]],
            page: int,
            *,
            all_groups: bool
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        with self.i18n.context():
            for group in groups:
                if "full_name" in group:
                    text: str = _("button.group_and_supervisor").format(
                        group_name=group["name"],
                        full_name=group.get("full_name")
                    )
                else:
                    text: str = _("button.group").format(
                        group_name=group["name"]
                    )

                builder.button(
                    text=text,
                    callback_data=GroupChoiceAction(group_id=group["id"]).pack()
                )

            if all_groups:
                builder.button(
                    text=_("button.all_groups"),
                    callback_data=GroupChoiceAction().pack()
                )

            builder.add(*self.button_factory.create_pagination_buttons(page))
            builder.add(self.button_factory.create_back_button())

        builder.adjust(*([1] * (len(groups) + 1 if all_groups else len(groups))), 2, 1)
        return builder.as_markup()
