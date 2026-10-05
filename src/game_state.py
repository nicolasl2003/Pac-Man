from __future__ import annotations
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from . import Level

from . import Config


class GameStateModel:
    """The state of the game containing basic infos.

    score -- The score of the current run
    highscore -- The highscore since the game was opened
    stage -- The current level index of the run
    level -- The current level object
    lives -- The current live of the player
    menu -- The current menu
    """

    score: int
    highscore: int
    stage: int
    level: Level
    lives: int
    menu: Any  # TODO

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        from mazegenerator import MazeGenerator
        from src import Maze, Level
        self.score = 0
        self.highscore = 0
        self.stage = 0
        self.level = Level(Maze(MazeGenerator(perfect=False).maze))
        self.lives = Config.lives
        self.menu = NotImplemented
