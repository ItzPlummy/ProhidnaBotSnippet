from abc import ABC, abstractmethod


class AbstractScene(ABC):
    @abstractmethod
    def on_menu(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    def on_back(
            self,
            *args,
            **kwargs
    ) -> None: pass

    @abstractmethod
    def on_scene_change(
            self,
            *args,
            **kwargs
    ) -> None: pass
