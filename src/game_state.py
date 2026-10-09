from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from . import Level

from random import Random


class GameStateModel:
    """The state of the game containing basic infos.

    random -- The random instance of the game
    score -- The score of the current run
    highscore -- The highscore since the game was opened
    stage -- The current level index of the run
    timer -- The time left before the end of the run
    level -- The current level object
    lives -- The current live of the player
    menu -- The current menu
    """

    random: Random
    score: int
    highscore: int
    stage: int
    timer: int
    level: Level
    lives: int
    menu: Any  # TODO

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        from mazegenerator import MazeGenerator
        from src import Config, Maze, Level
        self.random = Random(Config.seed)
        self.score = 0
        self.highscore = 0
        self.stage = 0
        self.timer = Config.level_time
        self.level = Level(Maze(MazeGenerator(perfect=False).maze))
        self.lives = Config.lives
        self.menu = NotImplemented
