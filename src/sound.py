import pygame


def management_sound() -> None:
    pygame.mixer.init()
    pygame.mixer.music.load("src/sounds/PacMan.mp3")
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.5)


def quit_sound() -> None:
    print("stop music")
    pygame.mixer.music.stop()
