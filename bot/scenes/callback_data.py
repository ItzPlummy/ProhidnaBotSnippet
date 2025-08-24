from typing import Any

from aiogram.filters.callback_data import CallbackData

from app.bot.enums.setting import Setting, BoolSetting


class AbstractAction(CallbackData, prefix="abstract"):
    pass


class MenuAction(AbstractAction, prefix="menu"):
    pass


class BackAction(AbstractAction, prefix="back"):
    pass


class ChangeSceneAction(AbstractAction, prefix="change_scene"):
    to_scene: str


class ChangeSettingAction(AbstractAction, prefix="change_setting"):
    setting: Setting
    value: Any


class ChangeBoolSettingAction(ChangeSettingAction, prefix="change_bool_setting"):
    setting: BoolSetting
    value: bool


class TryAgainAction(AbstractAction, prefix="try_again"):
    pass


class ChoiceAction(AbstractAction, prefix="choice"):
    choice: int


class GroupChoiceAction(AbstractAction, prefix="choice_group"):
    group_id: str | None = None


class StudentChoiceAction(AbstractAction, prefix="choice_student"):
    student_id: str | None = None


class CalendarChoiceAction(AbstractAction, prefix="choice_calendar"):
    pass


class CalendarDayChoiceAction(AbstractAction, prefix="choice_calendar_day"):
    year: int | None = None
    month: int | None = None
    day: int


class PageAction(AbstractAction, prefix="page"):
    page: int


class SendAction(AbstractAction, prefix="send"):
    pass


class CalendarConfirmAction(AbstractAction, prefix="calendar_confirm_action"):
    pass
