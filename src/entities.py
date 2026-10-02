from enum import Enum, auto
from typing import Any, Self
from . import CellNotFoundError, Cell, Maze, Direction


class Entity:
    """A generic entity class that stores common code for entities.

    spawn -- The cell used on respawn
    cell -- The cell the entity stands on
    position -- The graphical position of the entity
    """
    position: tuple[int, int]
    spawn: Cell
    cell: Cell

    def __init__(self, spawn: Cell) -> None:
        """Creates the entity.

        spawn -- The spawn cell of the entity
        """
        self.spawn = spawn
        self.respawn()

    def respawn(self) -> None:
        """Put the entity back on its spawn cell."""

        self.cell = self.spawn
        self.position = (self.cell.x, self.cell.y)


class Rotation(Enum):
    """The rotation angle of the visuals of the entity.

        UP -- The up rotation
        RIGHT -- The right rotation
        DOWN -- The down rotation
        LEFT -- The left rotation
    """

    UP = NotImplemented
    RIGHT = NotImplemented
    DOWN = NotImplemented
    LEFT = NotImplemented

    _TRANSFORM = {
        Direction.UP: UP,
        Direction.RIGHT: RIGHT,
        Direction.DOWN: DOWN,
        Direction.LEFT: LEFT
    }

    def next(self, direction: Direction) -> Self:
        try:
            return self.from_direction(direction)
        except KeyError:
            return self

    @classmethod
    def from_direction(cls, direction: Direction) -> Self:
        return cls._TRANSFORM[direction]


class RenderedEntity(Entity):
    """A generic entity class that stores common code for rendering.

    x -- The x position of the entity on screen
    y -- The y position of the entity on screen
    rotation -- The rotation angle of the visuals of the entity
    """

    x: int
    y: int
    rotation: Rotation
    image: Any  # TODO

    def update(self, delta_time: int) -> None:
        """Updates the visual of the entity.

        delta_time -- The time elapsed inbetween two frames
        """

        raise NotImplementedError  # TODO


class MovingEntity(Entity):
    """A generic entity class that stores common code for moving entities.

    direction -- The current direction
    """

    direction: Direction

    def respawn(self) -> None:
        """Put the entity back on its spawn cell."""
        super().respawn()
        self.direction = Direction.STILL

    def move(self, direction: Direction) -> bool:
        """Crosses cell toward a direction.

        direction -- The direction you move the entity

        Raises EntityBlockedError if a wall stops the entity
        """

        if not self.cell.can_move(direction): # Redundant ?
            return False

        from src import GameState

        maze: Maze = GameState.level.maze
        try:
            self.cell = maze.get_neighbor(self.cell, direction)
            return True
        except CellNotFoundError:
            return False

    def collides(self, other: Entity) -> bool:
        """Return whether both entities share a cell."""

        return bool(self.cell == other.cell)


class Ghost(MovingEntity, RenderedEntity):
    """Ghost starting from a maze corner.

    mode -- The current behaviour of the ghost
    respawn_cooldown -- The amount of time left before the ghost respawns
    edible_cooldown -- The cooldown for which the ghost is edible
    """

    class GhostMode(Enum):
        """The ghost behaviours.

        CHASE -- Chase mode
        EDIBLE -- Edible mode
        """

        CHASE = auto()
        EDIBLE = auto()
        DEAD = auto()

    mode: GhostMode
    respawn_cooldown: int
    edible_cooldown: int

    def __init__(self, spawn: Cell) -> None:
        """Creates the ghost.

        spawn -- The cell on which to spawn the ghost
        """
        super().__init__(spawn)
        self.respawn_cooldown = 0
        self.calm()

    def tick(self) -> None:
        match self.mode:
            case self.GhostMode.CHASE:
                pass
            case self.GhostMode.EDIBLE:
                self.edible_cooldown -= 1
            case self.GhostMode.DEAD:
                self.respawn_cooldown -= 1

    def frighten(self, cooldown: int) -> None:
        """Make the ghost edible for some time.

        cooldown -- The amount of time the ghost is edible for
        """

        self.mode = self.GhostMode.EDIBLE
        self.edible_cooldown = cooldown

    def calm(self) -> None:
        """End the edible state."""

        self.mode = self.GhostMode.CHASE

    def kill(self, respawn_cooldown: int) -> None:
        """Remove the ghost from the level until he respawns.

        respawn_cooldown -- The amount of time the ghost takes to respawn
        """

        self.mode = self.GhostMode.DEAD
        self.respawn_cooldown = respawn_cooldown
