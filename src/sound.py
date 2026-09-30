import pygame


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
