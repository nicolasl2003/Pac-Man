from typing import Optional
from .renderer import PygameRenderer

Color = tuple[int, int, int]


class Button:
    def __init__(self, x: int, y: int, width: int,
                 height: int, text: str, action: Optional[str] = None):
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.text: str = text
        self.action: Optional[str] = action
        self.is_hovered: bool = False

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

    def draw(self, renderer: PygameRenderer) -> None:
        base_color: Color = (70, 70, 200) if self.is_hovered else (40, 40, 120)
        text_color: Color = (255, 255, 255)
        renderer.draw_rect(self.x, self.y, self.width, self.height, base_color)

        text_x = self.x + 20
        text_y = self.y + self.height // 2 - 12
        renderer.draw_text(self.text, text_x, text_y, text_color)
