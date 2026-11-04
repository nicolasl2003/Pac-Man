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
        TIMEDOUT -- The level ran out of time, the run still playable
        """

        RUNNING = auto()
        WON = auto()
        LOST = auto()
        TIMEDOUT = auto()

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

            self.ghosts = [Ghost(maze.get_spawn(i), i % 4)
                           for i in range(ghost_count)
                           ]

        def _create_pacgums(pacgum_count: int, ss_pacgum_count: int) -> None:
            """Creates the level pacgum.

            pacgum_count -- The pacgum count of the level
            ss_pacgum_count -- The super pacgum count of the level
            """

            self.pacgums = []

            spawns: list[Cell] = [cell
                                  for cell in self.maze.cell_dict.values()
                                  if cell.accessible
                                  and cell not in self.maze.corners
                                  and cell != self.player.cell
                                  ]

            stride: int
            spawn: Cell

            try:
                stride = (len(spawns) // (ss_pacgum_count - 4)
                          if ss_pacgum_count < len(spawns)
                          else 1
                          )
            except ZeroDivisionError:
                stride = 0

            for idx in range(min(ss_pacgum_count, len(self.maze.corners))):
                spawn = self.maze.corners[idx]
                self.pacgums.append(SuperPacGum(spawn))

            for idx in range(min(ss_pacgum_count - len(self.maze.corners),
                                 len(spawns))):
                spawn = spawns.pop(idx * (stride - 1))
                self.pacgums.append(SuperPacGum(spawn))

            if pacgum_count == -1:
                pacgum_count = len(spawns)

            stride = (len(spawns) // pacgum_count
                      if 0 < pacgum_count < len(spawns)
                      else 1
                      )

            for idx in range(min(pacgum_count, len(spawns))):
                spawn = spawns.pop(idx * (stride - 1))
                self.pacgums.append(PacGum(spawn))

            for pacgum in self.pacgums:
                pacgum.stored = self.pacgums

        from src import Config, GameState

        self.maze = maze
        self.player = Player(self.maze.get_center())
        if Config.ghost_spawn == Config.GhostSpawnType.CLOSED_CELL:
            self.player.cell = GameState.random.sample(self.maze.corners, 1)[0]

        _create_ghosts(Config.ghost_count)
        _create_pacgums(Config.pacgum_count, Config.super_pacgum_count)
        GameState.reset_timer()
        self.state = Level.State.RUNNING

    def lost(self) -> State:
        """Loses the game."""

        self.state = Level.State.LOST
        return self.state

    def lose_life(self) -> None:
        """Takes a life from the player and sends everyone back to spawn."""

        from src import GameState

        GameState.lives -= 1
        if GameState.lives <= 0:
            self.lost()
            return
        self.player.respawn()
        for ghost in self.ghosts:
            ghost.respawn()

    def tick(self) -> State:
        """Ticks all the level members.

        Returns the level state after the tick
        """

        from src import GameState

        if self.state != Level.State.RUNNING:
            return self.state
        if GameState.timer == 0:
            self.state = Level.State.TIMEDOUT
            return self.state
        if not GameState.cheat:
            GameState.timer -= 1
        self.player.tick()
        for ghost in self.ghosts:
            ghost.tick()
        if not self.pacgums:
            self.state = Level.State.WON
        return self.state
