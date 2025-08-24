from enum import Enum


class Setting(Enum):
    pass


class BoolSetting(Setting):
    ALLOW_MESSAGES = "send_bot_messages"
    ALLOW_VARIATIONS = "allow_bot_variations"
