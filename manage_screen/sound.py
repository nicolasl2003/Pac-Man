import pygame
from typing import Any


def management_sound(volume: float, infinit: bool) -> None:
    pygame.mixer.init()
    print("init music")
    pygame.mixer.music.load("src/sounds/PacMan.mp3")
    if (infinit is True):
        pygame.mixer.music.play(-1)
    else:
        pygame.mixer.music.play(0)
    pygame.mixer.music.set_volume(volume)


def quit_sound() -> None:
    pygame.mixer.music.stop()


class SoundManager:
    _sounds: dict[str, Any] = {}

    @classmethod
    def load(cls, name: str, path: str) -> None:
        if (name not in cls._sounds):
            cls._sounds[name] = pygame.mixer.Sound(path)

    @classmethod
    def play(cls, name: str) -> None:
        sound = cls._sounds.get(name)
        if (sound is not None):
            sound.play()
