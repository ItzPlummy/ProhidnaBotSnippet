import random
from typing import Dict, List, Annotated

from aiogram.utils.i18n import gettext as _, I18n

from app.bot.variations.variation_type import VariationType
from app.services.config import Config

config = Config(_env_file=".env")
i18n = I18n(path=config.locale_path, default_locale=config.locale, domain=config.domain)


class Variations:
    def __init__(
            self
    ):
        with i18n.context():
            self.base_enter: str = _("schedule.enter.base")
            self.base_exit: str = _("schedule.exit.base")
            self.base_log_present: str = _("schedule.log.present.base")
            self.base_log_late: str = _("schedule.log.late.base")

            self.enter_variations: Dict[Annotated[bool, "Pass Type"], Dict[VariationType, List[str]]] = {
                True: {
                    VariationType.DEFAULT: [
                        _("schedule.enter.default.0"),
                        _("schedule.enter.default.1"),
                        _("schedule.enter.default.2"),
                        _("schedule.enter.default.3"),
                        _("schedule.enter.default.4"),
                        _("schedule.enter.default.5"),
                        _("schedule.enter.default.6"),
                        _("schedule.enter.default.7"),
                        _("schedule.enter.default.8"),
                        _("schedule.enter.default.9")
                    ],
                    VariationType.NIGHT: [
                        _("schedule.enter.night.0"),
                        _("schedule.enter.night.1"),
                        _("schedule.enter.night.2")
                    ]
                },
                False: {
                    VariationType.DEFAULT: [
                        _("schedule.exit.default.0"),
                        _("schedule.exit.default.1"),
                        _("schedule.exit.default.2"),
                        _("schedule.exit.default.3"),
                        _("schedule.exit.default.4"),
                        _("schedule.exit.default.5"),
                        _("schedule.exit.default.6"),
                        _("schedule.exit.default.7"),
                        _("schedule.exit.default.8"),
                        _("schedule.exit.default.9")
                    ],
                    VariationType.NIGHT: [
                        _("schedule.exit.night.0"),
                        _("schedule.exit.night.1"),
                        _("schedule.exit.night.2")
                    ]
                }
            }

            self.log_variations: Dict[VariationType, List[str]] = {
                VariationType.PRESENT: [
                    _("schedule.log.present.0"),
                    _("schedule.log.present.1"),
                    _("schedule.log.present.2"),
                    _("schedule.log.present.3"),
                    _("schedule.log.present.4")
                ],
                VariationType.LATE: [
                    _("schedule.log.late.0"),
                    _("schedule.log.late.1"),
                    _("schedule.log.late.2"),
                    _("schedule.log.late.3"),
                    _("schedule.log.late.4")
                ]
            }

    def get_enter_variation(
            self,
            allow_variations: bool,
            has_entered: bool,
            variation_type: VariationType
    ) -> str:
        if not allow_variations:
            return self.base_enter if has_entered else self.base_exit

        return random.choice(self.enter_variations[has_entered][variation_type])

    def get_log_variation(
            self,
            allow_variations: bool,
            variation_type: VariationType
    ) -> str:
        if not allow_variations:
            return self.base_log_present if variation_type == VariationType.PRESENT else self.base_log_late

        return random.choice(self.log_variations[variation_type])


variations = Variations()
