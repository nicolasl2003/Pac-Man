from abc import ABC, abstractmethod
from typing import Optional, Any
from .renderer import PygameRenderer, InputEvent


class Screen(ABC):
    @abstractmethod
    def on_enter(self, **kwargs: Any) -> None:
        pass

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        raise (NotImplementedError)

    @abstractmethod
    def update(self, dt: float) -> None:
        raise (NotImplementedError)

    @abstractmethod
    def draw(self, renderer: PygameRenderer) -> None:
        raise (NotImplementedError)
