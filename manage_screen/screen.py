from abc import ABC, abstractmethod
from typing import Optional
from .renderer import PygameRenderer, InputEvent


class Screen(ABC):
    """Define the common interface for game screens."""

    @abstractmethod
    def on_enter(self, **kwargs: PygameRenderer) -> None:
        """Prepare the screen when it becomes active.

        Args:
            **kwargs: Context values required to initialize the screen.
        """
        pass

    def handle_events(self, events: list[InputEvent]) -> Optional[str]:
        """Process input events and report any requested transition.

        Args:
            events: User input events to process.

        Returns:
            The next screen name, or None to remain on this screen.
        """
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update the screen state.

        Args:
            dt: Time elapsed since the previous update, in seconds.
        """
        pass

    @abstractmethod
    def draw(self, renderer: PygameRenderer) -> None:
        """Draw the screen using the provided renderer.

        Args:
            renderer: Renderer used to display the screen.
        """
        pass
