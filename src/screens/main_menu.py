from typing import Optional
from ..screen import Screen, InputEvent
from ..renderer import PygameRenderer
from ..button import Button


class MainMenuScreen(Screen):
    def __init__(self) -> None:
        self.buttons: list[Button] = [
            Button(220, 180, 200, 60, "START", action="GAME"),
            Button(220, 260, 200, 60, "HIGHSCORES", action="HIGHSCORES"),
            Button(220, 340, 200, 60, "QUIT", action="QUIT")
        ]

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        for event in events:
            if (event.kind == "QUIT"):
                return ("QUIT")
            if (event.kind == "KEY" and event.key == "ESCAPE"):
                return ("QUIT")

            for button in self.buttons:
                result = button.handle_event(event)
                if (result):
                    return (result)
        return (None)

    def update(self, dt: float) -> None:
        return (None)

    def draw(self, renderer: PygameRenderer):
        renderer.clear((0, 0, 0))
        renderer.draw_text("PAC-MAN", 200, 80, (255, 255, 0), big=True)

        for button in self.buttons:
            button.draw(renderer)
