from datetime import datetime
from typing import Any

from app.services.config import Config


class AttributedDict(dict):
    config = Config(_env_file=".env")
    datetime_format = config.datetime_format

    def __init__(
            self,
            dictionary: dict,
            **kwargs
    ) -> None:
        super().__init__(dictionary, **kwargs)

        for key, value in dictionary.items():
            setattr(self, str(key), self.__process_value__(value))

    def __getattr__(
            self,
            item: str
    ) -> Any:
        return self.__dict__.get(item)

    def __process_value__(
            self,
            value: Any
    ) -> Any:
        if isinstance(value, dict):
            return AttributedDict(value)

        if isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
            return [self.__process_value__(item) for item in value]

        if isinstance(value, str):
            try:
                return datetime.strptime(value, self.datetime_format)
            except ValueError:
                pass

        return value
