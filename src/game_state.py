from __future__ import annotations

from typing import TYPE_CHECKING

from src import Config

if TYPE_CHECKING:
    from . import Level

from random import Random


class GameStateModel:
    """The state of the game containing basic infos.

    random -- The random instance of the game
    score -- The score of the current run
    highscore -- The best score saved or reached since the game opened
    stage -- The current level index of the run
    timer -- The number of  ticks left before the end of the level
    level -- The current level object
    lives -- The current live of the player
    """

    random: Random
    score: int
    highscore: int
    stage: int
    timer: int
    level: Level
    lives: int

    # Hardcoded number of stages
    _STAGE_COUNT = 10

    @property
    def timer_s(self) -> int:
        """Returns the time left in seconds."""

        return self.timer * Config.ms_per_tick // 1000

    def __init__(self) -> None:
        """Creates the state, before any highscore is known."""

        self.highscore = 0

    def reset(self) -> None:
        """Launches a new game data wise."""

        from src.scores import load_scores
        self.random = Random(Config.seed)
        self.score = 0
        best_saved: int = max((row["score"] for row in load_scores()),
                              default=0)
        self.highscore = max(self.highscore, best_saved)
        self.stage = 1
        self.reset_timer()
        self._build_level(Config.seed)
        self.lives = Config.lives

    def next_stage(self) -> bool:
        """Transitions from one stage to another

        Returns False when the last level was already reached
        """

        if self.stage + 1 >= self._STAGE_COUNT:
            return False
        self.stage += 1
        self._build_level(int(f"{Config.seed}{self.stage}"))
        return True

    def _build_level(self, seed: int) -> None:
        """Builds a game level

        seed -- The seed handed to the MazeGenerator

        Raises GeneratorError when an invalid maze is generated
        """

        from mazegenerator import MazeGenerator
        from src import GeneratorError, Level, Maze

        try:
            grid: list[list[int]] = MazeGenerator(perfect=False,
                                                  seed=seed).maze
        except Exception as e:
            raise GeneratorError(f"The maze generator failed: {e}") from None
        if not grid or not grid[0]:
            raise GeneratorError("The maze generator gave an empty maze")
        self.level = Level(Maze(grid))

    def reset_timer(self) -> None:
        """Resets the game timer."""

        self.timer = Config.level_time * 1000 // Config.ms_per_tick
