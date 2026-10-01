from mazegenerator import MazeGenerator

from . import Config, Maze, Level
from typing import Any


class GameStateModel:
    """The state of the game containing basic infos.

    score -- The score of the current run
    highscore -- The highscore since the game was opened
    lives -- The current live of the player
    menu -- The current menu
    """

    score: int
    highscore: int
    level: int
    level_object: Level
    lives: int
    menu: Any  # TODO

    def __init__(self) -> None:
        self.score = 0
        self.highscore = 0
        self.level = 0
        self.level_object = Level(Maze(MazeGenerator(perfect=False).maze))
        self.lives = Config.lives
        self.menu = NotImplemented

    @staticmethod
    def reset() -> None:
        global GameState
        GameState = GameStateModel()


GameState: GameStateModel = GameStateModel()
