from typing import Optional, Any
import pygame
from .renderer import InputEvent
from .sound import SoundManager
from functools import lru_cache

Color = tuple[int, int, int]


class Button:
    """Represent an interactive button displayed on a game screen."""

    def __init__(self, x: int, y: int, width: int,
                 height: int, text: str, action: Optional[str] = None,
                 gost_path: str = "src/img/enemy_blue.png"):
        """Create a button with its bounds, label, and optional action.

        Args:
            x: Horizontal coordinate of the top-left corner.
            y: Vertical coordinate of the top-left corner.
            width: Button width in pixels.
            height: Button height in pixels.
            text: Label displayed on the button.
            action: Identifier returned after a valid click.
            gost_path: Path to the image displayed while hovering.
        """
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
        """Load and scale the hover image if it has not been loaded yet."""
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
        """Process an input event and return any triggered action.

        Args:
            event: Keyboard or mouse event to process.

        Returns:
            The button action after a valid click, or None otherwise.
        """
        if (event.kind == "MOTION" and event.pos):
            self.update_hover(*event.pos)
        elif (event.kind == "CLICK" and event.pos):
            try:
                SoundManager.play("click")
            except pygame.error as e:
                print(e)
            return (self.handle_click(*event.pos))
        return (None)

    def contains_point(self, mouse_x: int, mouse_y: int) -> bool:
        """Check whether a point lies within the button bounds.

        Args:
            mouse_x: Horizontal coordinate of the point.
            mouse_y: Vertical coordinate of the point.

        Returns:
            True if the point is inside the button, False otherwise.
        """
        inside_x = self.x <= mouse_x <= self.x + self.width
        inside_y = self.y <= mouse_y <= self.y + self.height
        return (inside_x and inside_y)

    def update_hover(self, mouse_x: int, mouse_y: int) -> None:
        """Update the hover state based on the pointer position.

        Args:
            mouse_x: Horizontal coordinate of the pointer.
            mouse_y: Vertical coordinate of the pointer.
        """
        self.is_hovered = self.contains_point(mouse_x, mouse_y)

    def handle_click(self, mouse_x: int, mouse_y: int) -> Optional[str]:
        """Return the button action if the click falls inside its bounds.

        Args:
            mouse_x: Horizontal coordinate of the click.
            mouse_y: Vertical coordinate of the click.

        Returns:
            The button action for a valid click, or None otherwise.
        """
        if (self.contains_point(mouse_x, mouse_y)):
            return (self.action)
        return (None)

    @lru_cache
    def _compute_font_size(self, renderer: Any) -> int:
        """Find the largest font size that fits the button label.

        Args:
            renderer: Renderer used to measure the text.

        Returns:
            Font size in points.
        """
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
        """Draw the button, its label, and its hover indicator.

        Args:
            renderer: Renderer used to draw the button.
        """
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
