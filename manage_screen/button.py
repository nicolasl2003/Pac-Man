from typing import Optional, Any
import pygame
from .renderer import InputEvent
from .sound import SoundManager

Color = tuple[int, int, int]


class Button:
    def __init__(self, x: int, y: int, width: int,
                 height: int, text: str, action: Optional[str] = None,
                 gost_path: str = "src/img/enemy_bleu-remove.png"):
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.text: str = text
        self.action: Optional[str] = action
        self.is_hovered: bool = False

        self.font_size: int = int(self.height * 0.5)
        self.gost_image: Optional[pygame.Surface] = None
        self.gost_path = gost_path

    def load_ghost(self) -> None:
        if (self.gost_image is None):
            try:
                image = pygame.image.load(self.gost_path).convert_alpha()
                gost_size = int(self.height * 0.9)
                self.gost_image = pygame.transform.scale(image, (gost_size,
                                                                 gost_size))
            except (pygame.error, FileNotFoundError):
                self.gost_image = None
                print("Error image")

    def handle_event(self, event: InputEvent) -> Optional[str]:
        if (event.kind == "MOTION" and event.pos):
            self.update_hover(*event.pos)
        elif (event.kind == "CLICK" and event.pos):
            SoundManager.play("click")
            return (self.handle_click(*event.pos))
        return (None)

    def contains_point(self, mouse_x: int, mouse_y: int) -> bool:
        inside_x = self.x <= mouse_x <= self.x + self.width
        inside_y = self.y <= mouse_y <= self.y + self.height
        return (inside_x and inside_y)

    def update_hover(self, mouse_x: int, mouse_y: int) -> None:
        self.is_hovered = self.contains_point(mouse_x, mouse_y)

    def handle_click(self, mouse_x: int, mouse_y: int) -> Optional[str]:
        if (self.contains_point(mouse_x, mouse_y)):
            return (self.action)
        return (None)

    def _compute_font_size(self, renderer: Any) -> int:
        max_font_size = int(self.height * 0.5)
        padding = int(self.width * 0.1)
        available_width = self.width - padding

        font_size = max_font_size
        while (font_size > 5):
            text_width, _ = renderer.get_text_size(self.text, font_size)
            if (text_width <= available_width):
                break
            font_size -= 1

        return (font_size)

    def draw(self, renderer: Any) -> None:
        base_color: Color = (0, 0, 0) if self.is_hovered else (0, 0, 0)
        text_color: Color = (255, 255, 100) if self.is_hovered else (255, 255,
                                                                     255)
        renderer.draw_rect(self.x, self.y, self.width, self.height, base_color)

        font_size = self._compute_font_size(renderer)
        text_width, text_height = renderer.get_text_size(self.text, font_size)
        text_x = self.x + (self.width - text_width) // 2
        text_y = self.y + (self.height - text_height) // 2

        renderer.draw_text(self.text, text_x, text_y, text_color, font_size)

        if (self.is_hovered):
            self.load_ghost()
            if (self.gost_image is not None):
                spacing_x = int(self.width * 0.2)
                spacing_y = int(self.height * 0.5)
                ghost_x = text_x - spacing_x
                ghost_y = (
                    self.y
                    + (self.height - (self.gost_image.get_height() // 2))
                    - spacing_y
                )
                renderer.screen.blit(self.gost_image, (ghost_x, ghost_y))
