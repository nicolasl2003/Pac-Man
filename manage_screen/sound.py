import sys
import pygame
from typing import Any


def management_sound(volume: float, infinit: bool) -> None:
    """Initialize and play the background music.

    Args:
        volume: Playback volume between 0.0 and 1.0.
        infinit: Whether to loop the music indefinitely.
    """
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("src/sounds/PacMan.mp3")
        if (infinit is True):
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.play(0)
        pygame.mixer.music.set_volume(volume)
    except pygame.error as e:
        print(e, file=sys.stderr)


def quit_sound() -> None:
    """Stop the currently playing music, if a sound device was found."""
    if (pygame.mixer.get_init()):
        pygame.mixer.music.stop()


class SoundManager:
    """Load and play the game's sound effects."""

    _sounds: dict[str, Any] = {}

    @classmethod
    def load(cls, name: str, path: str) -> None:
        """Load a sound effect unless it is already cached.

        Args:
            name: Key used to retrieve the sound effect.
            path: Path to the audio file.
        """
        if (name not in cls._sounds):
            cls._sounds[name] = pygame.mixer.Sound(path)

    @classmethod
    def play(cls, name: str) -> None:
        """Play the loaded sound effect associated with a key.

        Args:
            name: Key of the sound effect to play.
        """
        sound = cls._sounds.get(name)
        if (sound is not None):
            sound.play()
