from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import Cell, Maze, PacGum, SuperPacGum, Ghost, Player

from enum import Enum, auto


class Level:
    """A level of pacman.

    ghosts -- The ghosts of the level
    pacgums -- The pacgums in the level
    player -- The player object
    maze -- The maze instance
    state -- The level state
    """

    class State(Enum):
        """The level state.

        RUNNING -- The game is still running
        WON -- The level was won by the player
        LOST -- The player died
        """

        RUNNING = auto()
        WON = auto()
        LOST = auto()

    ghosts: list[Ghost]
    pacgums: list[PacGum | SuperPacGum]
    player: Player
    maze: Maze
    state: State

    def __init__(self, maze: Maze) -> None:
        """Creates a new level.

        maze -- The maze map to assign to the level
        """

        from src import PacGum, SuperPacGum, Ghost, Player

        def _create_ghosts(ghost_count: int) -> None:
            """Creates the level ghosts.

            ghost_count -- The ghost count of the level
            """

            self.ghosts = [Ghost(maze.get_spawn(i))
                           for i in range(ghost_count)
                           ]

        def _create_pacgums(pacgum_count: int, ss_pacgum_count: int) -> None:
            """Creates the level pacgum.

            pacgum_count -- The pacgum count of the level
            ss_pacgum_count -- The super pacgum count of the level
            """

            spawns: list[Cell] = [cell
                                  for cell in self.maze.cell_dict.values()
                                  if cell.accessible
                                  and cell not in self.maze.corners
                                  ]

            score: int = (len(spawns) // (ss_pacgum_count - 4)
                          if ss_pacgum_count < len(spawns)
                          else 1
                          )

            for cell in self.maze.corners:
                self.pacgums.append(SuperPacGum(cell))

            for idx in range(ss_pacgum_count):
                spawn: Cell = spawns.pop(idx * (score - 1))
                self.pacgums.append(SuperPacGum(spawn))

            score = (len(spawns) // pacgum_count
                     if pacgum_count < len(spawns)
                     else 1
                     )

            for idx in range(pacgum_count):
                spawn = spawns.pop(idx * (score - 1))
                self.pacgums.append(PacGum(spawn))

        from src import Config, GameState

        self.maze = maze
        self.player = Player(self.maze.get_cell((0, 0)))

        if Config.ghost_spawn == Config.GhostSpawnType.CLOSED_CELL:
            self.player.cell = GameState.random.sample(self.maze.corners, 1)[0]
        elif Config.ghost_spawn == Config.GhostSpawnType.CORNERS:
            pass  # TODO: Handle maze size to always spawn in the middle

        _create_ghosts(Config.ghost_count)
        _create_pacgums(Config.pacgum_count, Config.ss_pacgum_count)
        GameState.timer = Config.level_time
        self.state = Level.State.RUNNING

    def lost(self) -> None:
        """Loses the game."""

        self.state = Level.State.LOST

    def tick(self) -> State:
        """Ticks all the level members."""

        from src import GameState

        if GameState.timer <= 0:
            self.lost()
        GameState.timer -= 1
        self.player.tick()
        for ghost in self.ghosts:
            ghost.tick()
        return self.state

    def update(self, delta_time: int) -> None:
        """Updates the graphic aspect of the level.

        delta_time -- The time spent since last frame
        """

        # TODO: draw level or remove
        self.maze.update(delta_time)
        for ghost in self.ghosts:
            ghost.update(delta_time)
        self.player.update(delta_time)
