from . import config
from manage_screen.renderer import PygameRenderer
from manage_screen.screen import Screen
from .screens.main_menu import MainMenuScreen
from .screens.highscores import HighscoresScreen
from .screens.game_over import GameOverScreen
from .screens.game import Games
from .screens.instruction import InstructionsScreen
from .screens.pause import PauseScreen

import sys


def main() -> None:
    try:
        config.ConfigModel.load_from_file("config.json")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    renderer = PygameRenderer(config.Config.screen_width, config.
                              Config.screen_height, "Pac-Man 42")
    screens: dict[str, Screen] = {
        "MENU": MainMenuScreen(),
        "HIGHSCORES": HighscoresScreen(),
        "GAMEOVER": GameOverScreen(),
        "GAME": Games(),
        "INSTRUCTIONS": InstructionsScreen(),
        "PAUSE": PauseScreen()
    }
    current: str = "MENU"
    running = True

    screens[current].on_enter(renderer=renderer)
    while (running):
        events = renderer.poll_events()
        result = screens[current].handle_events(events)

        next_screen = None
        if (isinstance(result, tuple)):
            next_screen, _ = result
        elif (isinstance(result, str)):
            next_screen = result

        if (next_screen == "QUIT"):
            running = False
        elif (next_screen is not None):
            if (next_screen in screens):
                current = next_screen
                screens[current].on_enter(renderer=renderer)
            else:
                print(f"[WARN] Screen '{next_screen}' not yet implemented.")

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
