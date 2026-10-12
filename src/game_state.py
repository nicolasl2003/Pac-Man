from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from . import Level

from random import Random


class GameStateModel:
    """The state of the game containing basic infos.

    random -- The random instance of the game
    score -- The score of the current run
    highscore -- The best score saved or reached since the game opened
    stage -- The current level index of the run
    timer -- The ticks left before the end of the level
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
        """Creates the state, before any highscore is known."""

        self.highscore = 0

    def reset(self) -> None:
        from mazegenerator import MazeGenerator
        from src import Config, Maze, Level
        from src.scores import load_scores
        self.random = Random(Config.seed)
        self.score = 0
        best_saved: int = max((row["score"] for row in load_scores()),
                              default=0)
        self.highscore = max(self.highscore, best_saved)
        self.stage = 0
        self.timer = Config.to_ticks(Config.level_time)
        self.level = Level(Maze(MazeGenerator(perfect=False,
                                              seed=Config.seed).maze))
        self.lives = Config.lives
        self.menu = NotImplemented
