from .renderer import PygameRenderer
from .screen import Screen
from .screens.main_menu import MainMenuScreen
from .screens.highscores import HighscoresScreen
from .screens.game_over import GameOverScreen
import sys


def main() -> None:
    renderer = PygameRenderer(640, 480, "Pac-Man 42")
    screens: dict[str, Screen] = {
        "MENU": MainMenuScreen(),
        "HIGHSCORES": HighscoresScreen(),
        "GAMEOVER": GameOverScreen(),
    }
    current: str = "MENU"
    running = True

    while (running):
        events = renderer.poll_events()
        result = screens[current].handle_events(events)

        next_screen = None
        data: dict = {}
        if (isinstance(result, tuple)):
            next_screen, data = result
        elif (isinstance(result, str)):
            next_screen = result

        if (next_screen == "QUIT"):
            running = False
        elif (next_screen is not None):
            if (next_screen in screens):
                current = next_screen
                screens[current].on_enter(**data)
            else:
                print(f"[WARN] Ecran '{next_screen}' pas encore implemter.")

        screens[current].update(renderer.clock.get_time() / 1000.0)
        screens[current].draw(renderer)
        renderer.present()

        renderer.clock.tick(60)

    renderer.close()


if (__name__ == "__main__"):
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(1)
