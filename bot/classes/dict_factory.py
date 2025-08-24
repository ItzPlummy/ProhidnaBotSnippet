from typing import Dict, Annotated, List

from aiogram.utils.i18n import lazy_gettext as __, I18n

from app.bot.enums.setting import BoolSetting, Setting
from app.statistics.enums.arrival_type import ArrivalType
from app.statistics.enums.excuse_type import ExcuseType


class DictFactory:
    def __init__(
            self,
            i18n: I18n
    ) -> None:
        self.i18n = i18n

    def create_start_dict(self) -> Dict[str, str]:
        with self.i18n.context():
            return {
                "administrator": __("menu.administrator").value,
                "manager": __("menu.manager").value,
                "supervisor": __("menu.supervisor").value,
                "parent": __("menu.parent").value
            }

    def create_verification_dict(self) -> Dict[str, str]:
        with self.i18n.context():
            return {
                "administrator": __("authorized.administrator").value,
                "manager": __("authorized.manager").value,
                "supervisor": __("authorized.supervisor").value,
                "parent": __("authorized.parent").value
            }

    def create_logs_dict(self) -> Dict[str, str]:
        with self.i18n.context():
            return {
                "entries": __("log.entries_page").value,
                "log": __("log.logs_page").value,
                "stats": __("log.stats_page").value
            }

    def create_has_entered_dict(self) -> Dict[Annotated[bool, "Pass Time"], str]:
        with self.i18n.context():
            return {
                True: __("entries.record.entered").value,
                False: __("entries.record.exited").value
            }

    def create_settings_button_dict(self) -> Dict[BoolSetting, Dict[bool, str]]:
        with self.i18n.context():
            return {
                BoolSetting.ALLOW_MESSAGES: {
                    True: __("button.settings.allow_messages.1").value,
                    False: __("button.settings.allow_messages.0").value
                },
                BoolSetting.ALLOW_VARIATIONS: {
                    True: __("button.settings.allow_variations.1").value,
                    False: __("button.settings.allow_variations.0").value
                }
            }

    def create_settings_answer_dict(self) -> Dict[Setting, Dict[bool, str]]:
        with self.i18n.context():
            return {
                BoolSetting.ALLOW_MESSAGES: {
                    True: __("answer.settings.allow_messages.1").value,
                    False: __("answer.settings.allow_messages.0").value
                },
                BoolSetting.ALLOW_VARIATIONS: {
                    True: __("answer.settings.allow_variations.1").value,
                    False: __("answer.settings.allow_variations.0").value
                }
            }

    def create_arrival_type_dict(self) -> Dict[ArrivalType, str]:
        with self.i18n.context():
            return {
                ArrivalType.PRESENT: __("arrival_type.present").value,
                ArrivalType.LATE: __("arrival_type.late").value,
                ArrivalType.ABSENT: __("arrival_type.absent").value
            }

    def create_excuses_dict(self) -> Dict[ExcuseType, str]:
        with self.i18n.context():
            return {
                ExcuseType.ESTEEMED_REASON: __("excuse.esteemed_reason").value,
                ExcuseType.AIR_ALERT: __("excuse.air_alert").value
            }

    def create_weekdays(self) -> List[str]:
        with self.i18n.context():
            return [
                "Понеділок",
                "Вівторок",
                "Середа",
                "Четвер",
                "П'ятниця",
                "Субота",
                "Неділя"
            ]
