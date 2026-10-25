from __future__ import annotations

from typing import TYPE_CHECKING

from src import Config

if TYPE_CHECKING:
    from . import Level

from random import Random


class GameStateModel:
    """The state of the game containing basic infos.

    cheat -- Whether the cheat mode is activated
    random -- The random instance of the game
    score -- The score of the current run
    highscore -- The best score saved or reached since the game opened
    stage -- The current level index of the run
    timer -- The number of  ticks left before the end of the level
    level -- The current level object
    lives -- The current live of the player
    """

    cheat: bool
    random: Random
    score: int
    highscore: int
    stage: int
    timer: int
    level: Level
    lives: int

    @property
    def timer_s(self) -> int:
        """Returns the time left in seconds."""

        return self.timer * Config.ms_per_tick // 1000

    @property
    def tick_ms(self) -> int:
        """Returns how long one game tick lasts, in milliseconds.

        Cheating game move up to 100ms faster than vanilla game
        """

        if not self.cheat:
            return Config.ms_per_tick

        return max(Config.ms_per_tick, min(Config.ms_per_tick, 100))

    def __init__(self) -> None:
        """Creates the game state before any game started."""

        self.highscore = 0
        self.cheat = False

    def reset(self) -> None:
        """Launches a new game data wise."""

        from mazegenerator import MazeGenerator
        from src import Config, Maze, Level
        from src.scores import load_scores
        self.random = Random(Config.seed)
        self.score = 0
        best_saved: int = max((row["score"] for row in load_scores()),
                              default=0)
        self.highscore = max(self.highscore, best_saved)
        self.stage = 0
        self.reset_timer()
        self.level = Level(Maze(MazeGenerator(perfect=False,
                                              seed=Config.seed).maze))
        self.lives = Config.lives

    def reset_timer(self) -> None:
        """Resets the game timer."""

        self.timer = Config.level_time * 1000 // Config.ms_per_tick
