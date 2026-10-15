import sys
from argparse import ArgumentParser

import pygame

from manage_screen.renderer import PygameRenderer
from manage_screen.screen import Screen
from .screens.game import Games
from .screens.game_over import GameOverScreen
from .screens.highscores import HighscoresScreen
from .screens.instruction import InstructionsScreen
from .screens.main_menu import MainMenuScreen
from .screens.pause import PauseScreen


def main(config_path: str) -> None:
    """Load the configuration and run the main game loop.

    config_path -- The path of the JSON configuration file
    """

    from . import Config, GameState

    try:
        Config.load_from_file(config_path)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    # The level built at import used the default config
    GameState.reset()
    renderer = PygameRenderer(Config.screen_width,
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

        screens[current].update(float(renderer.clock.get_time()))
        screens[current].draw(renderer)
        renderer.present()

        renderer.clock.tick(Config.frame_rate)

    renderer.close()


def run(argv: list[str]) -> None:
    """Checks the command line then runs the game.

    argv -- The command line, the configuration file as only argument
    """

    parser: ArgumentParser = ArgumentParser(prog=f"python3 {argv[0]}")
    parser.add_argument("config", help="path of the JSON configuration file")
    config_path: str = parser.parse_args(argv[1:]).config
    try:
        main(config_path)
    except KeyboardInterrupt:
        print("Interrupted by user")
        sys.exit(1)
    except pygame.error as e:
        print(f"Rendering error {e}")
        sys.exit(1)


if (__name__ == "__main__"):
    run(sys.argv)
