from typing import Optional
from ..screen import Screen
from ..renderer import PygameRenderer, InputEvent
from ..button import Button
from ..scores import save_score


class Games(Screen):
    def __init__(self) -> None:
        self.score: int = 0
        self.saved: bool = False

    def on_enter(self, **kwargs) -> None:
        pass

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")
        return (None)

    def update(self, dt: float) -> None:
        pass

    def draw(self, renderer: PygameRenderer) -> None:
        renderer.clear((0, 0, 0))
