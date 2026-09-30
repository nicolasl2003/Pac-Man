from typing import Optional
import pygame
from ..screen import Screen, InputEvent
from ..renderer import PygameRenderer
from ..button import Button
from ..sound import management_sound, quit_sound


class MainMenuScreen(Screen):
    def __init__(self) -> None:
        self.buttons: list[Button] = [
            Button(220, 180, 200, 60, "START", action="GAME"),
            Button(220, 260, 200, 60, "HIGHSCORES", action="HIGHSCORES"),
            Button(220, 260, 200, 60, "INSTRUCTIONS", action="INSTRUCTIONS"),
            Button(220, 340, 200, 60, "QUIT", action="QUIT")
        ]
        self.logo: Optional[pygame.Surface] = None
        self.logo_path = "src/img/logo.png"
        management_sound(0.7, True)

    def on_enter(self, **kwargs) -> None:
        renderer: PygameRenderer = kwargs.get("renderer")
        if (renderer is None):
            return

        screen_width = renderer.width
        screen_height = renderer.height

        if (self.logo is None):
            try:
                raw_logo = renderer.load_image(self.logo_path)
                original_width, original_height = raw_logo.get_size()
                aspect_ratio = original_width / original_height
                logo_width = int(screen_width * 0.4)
                logo_height = int(logo_width / aspect_ratio)
                self.logo = renderer.scale_image(raw_logo, logo_width,
                                                 logo_height)
            except FileNotFoundError as exc:
                print(f"[WARN] {exc}")

        bouton_width = int(screen_width * 0.37)
        button_height = int(screen_height * 0.09)
        spacing = int(screen_height * 0.04)

        label_actions = [
            ("START", "GAME"),
            ("HIGHSCORES", "HIGHSCORES"),
            ("INSTRUCTIONS", "INSTRUCTIONS"),
            ("QUIT", "QUIT"),
        ]

        total_height = len(label_actions) * button_height + (len(label_actions)
                                                             - 1) * spacing
        start_y = (screen_height - total_height) // 2 + 80

        self.buttons = []
        for i, (label, action) in enumerate(label_actions):
            x = (screen_width - bouton_width) // 2
            y = start_y + i * (button_height + spacing)
            self.buttons.append(Button(x, y, bouton_width, button_height,
                                       label, action=action))

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        for event in events:
            if (event.kind == "QUIT"):
                quit_sound()
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

        if (self.logo is None):
            try:
                self.logo = renderer.load_image(self.logo_path)
                self.logo = renderer.scale_image(self.logo, 300, 100)
            except FileNotFoundError as exc:
                print(f"[WARN] {exc}")

        if (self.logo is not None):
            center_x = renderer.width // 2
            renderer.center_image(self.logo, center_x,
                                  int(renderer.height * 0.12))

        for button in self.buttons:
            button.draw(renderer)
