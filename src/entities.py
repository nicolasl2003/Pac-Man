from enum import Enum, auto
from typing import Any

from . import CellNotFoundError, Cell, Maze, Direction, Config


class Entity:
    """A generic entity class that stores common code for entities.

    stored -- The container the entity in stored in
    spawn -- The cell used on respawn
    cell -- The cell the entity stands on
    """

    stored: list[Any]
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

    def next(self, direction: Direction) -> Any:
        """Retrieves the rotation to have on a direction change.

        direction -- The direction to use to determine the rotation
        """

        try:
            return self.from_direction(direction)
        except KeyError:
            return self

    @classmethod
    def from_direction(cls, direction: Direction) -> Any:
        """Transforms a direction into a rotation.

        direction -- The direction to use to determine the rotation

        Raises KeyError if the direction has no corresponding rotation
        """
        return DirectionToRotation[direction]


DirectionToRotation: dict[Direction, Rotation] = {
    Direction.UP: Rotation.UP,
    Direction.RIGHT: Rotation.RIGHT,
    Direction.DOWN: Rotation.DOWN,
    Direction.LEFT: Rotation.LEFT
}


class RenderedEntity(Entity):
    """A generic entity class that stores common code for rendering.

    x -- The x position of the entity on screen
    y -- The y position of the entity on screen
    rotation -- The rotation angle of the visuals of the entity
    """

    x: int
    y: int
    shown: bool
    rotation: Rotation
    image: Any  # TODO

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "cell" and isinstance(value, Cell):
            self.x = value.x
            self.y = value.y
        super().__setattr__(name, value)

    def respawn(self) -> None:
        super().respawn()
        self.x = self.cell.x
        self.y = self.cell.y
        self.rotation = Rotation.RIGHT
        self.image = NotImplemented  # TODO

    def update(self, delta_time: int) -> None:
        """Updates the visual of the entity.

        delta_time -- The time elapsed inbetween two frames
        """

        raise NotImplementedError  # TODO


class NotEdibleError(Exception):
    """Error when an entity cannot be eaten."""

    def __init__(self, entity: Entity):
        """Creates the error.

        entity -- The entity you tried to eat
        """

        super().__init__(f"Cannot eat the entity {entity}")


class EdibleEntity(RenderedEntity):
    """A generic entity class that can be eaten by the player.

    edible -- Whether the entity can be eaten or not
    prize --  The amount of points given to the player if eaten
    """

    edible: bool
    prize: int

    def __init__(self, spawn: Cell, points: int):
        """Creates the entity.

        spawn -- The cell on which the entity appears
        points -- The prize given to the player when eaten
        """

        super().__init__(spawn)
        self.prize = points

    def eat(self) -> int:
        """Eats the entity to oblivion.

        Raises NotEdibleError if the entity is not eatable
        """

        if not self.edible:
            raise NotEdibleError(self)

        self.stored.remove(self)
        return self.prize


class MovingEntity(RenderedEntity):
    """A generic entity class that stores common code for moving entities.

    direction -- The current direction
    can_collide -- Can the entity collide with another
    """

    direction: Direction
    can_collide: bool

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name == "direction" and isinstance(value, Direction):
            self.update_rotation()

    def update_rotation(self) -> None:
        """Updates the entity rotation accordingly to the direction."""

        self.rotation = self.rotation.next(self.direction)

    def respawn(self) -> None:
        """Put the entity back on its spawn cell."""

        super().respawn()
        self.direction = Direction.STILL
        self.can_collide = True

    def move(self, direction: Direction) -> bool:
        """Crosses cell toward a direction.

        direction -- The direction you move the entity

        Raises EntityBlockedError if a wall stops the entity
        """

        if not self.cell.can_move(direction):  # Redundant ?
            return False

        from src import GameState

        maze: Maze = GameState.level.maze
        try:
            self.cell = maze.get_neighbor(self.cell, direction)
            return True
        except CellNotFoundError:
            return False

    def collides(self, other: Entity) -> bool:
        """Return whether both entities collide on a cell."""

        if not self.can_collide:
            return False

        if isinstance(other, MovingEntity) and not other.can_collide:
            return False

        return True if self.cell == other.cell else False


class PacGum(EdibleEntity):
    """Pacgum class that is edible."""

    def __init__(self, spawn: Cell) -> None:
        """Creates the pacgum.

        spawn -- The cell on which the entity appears
        """

        super().__init__(spawn, Config.pacgum_points)


class SuperPacGum(EdibleEntity):
    """Super Pacgum class that is edible."""

    def __init__(self, spawn: Cell) -> None:
        """Creates the super pacgum.

        spawn -- The cell on which the entity appears
        """

        super().__init__(spawn, Config.ss_pacgum_points)


class Ghost(MovingEntity, EdibleEntity):
    """Ghost class of the game.

    mode -- The current behavior of the ghost
    respawn_cooldown -- The amount of time left before the ghost respawns
    edible_cooldown -- The cooldown for which the ghost is edible
    """

    class GhostMode(Enum):
        """The ghost behaviors.

        CHASE -- Chase mode
        EDIBLE -- Edible mode
        """

        CHASE = auto()
        EDIBLE = auto()
        DEAD = auto()

    mode: GhostMode
    respawn_cooldown: int
    edible_cooldown: int

    _LOCKED_ROTATIONS = [Rotation.RIGHT, Rotation.LEFT]

    def __init__(self, spawn: Cell) -> None:
        """Creates the ghost.

        spawn -- The cell on which to spawn the ghost
        """

        super().__init__(spawn, Config.ghost_points)

    def update_rotation(self) -> None:
        """Updates the entity rotation accordingly to the direction."""

        if self.rotation.next(self.direction) in self._LOCKED_ROTATIONS:
            self.rotation = self.rotation.next(self.direction)

    def respawn(self) -> None:
        """Puts the entity back on its spawn cell."""

        super().respawn()
        self.respawn_cooldown = 0
        self.calm()

    def tick(self) -> None:
        """Steps the ghost logic by one."""

        def _move() -> None:
            """Moves the ghost following a pattern."""

            from random import Random
            self.move(Random().sample(list(Direction), 1)[0])

        match self.mode:
            case self.GhostMode.CHASE:
                _move()
            case self.GhostMode.EDIBLE:
                if self.edible_cooldown == 0:
                    self.calm()
                    return
                self.edible_cooldown -= 1
            case self.GhostMode.DEAD:
                if self.respawn_cooldown == 0:
                    self.respawn()
                    return
                self.respawn_cooldown -= 1

    def frighten(self) -> None:
        """Makes the ghost edible for some time.

        cooldown -- The amount of time the ghost is edible for
        """

        self.mode = self.GhostMode.EDIBLE
        self.edible_cooldown = Config.ghost_edible_cooldown
        self.edible = True

    def calm(self) -> None:
        """Puts the ghost back into chase mode."""

        self.edible = False
        self.mode = self.GhostMode.CHASE

    def eat(self) -> int:
        """Remove the ghost from the level until he respawns."""

        if not self.edible:
            raise NotEdibleError(self)

        self.mode = self.GhostMode.DEAD
        self.edible = False
        self.respawn_cooldown = Config.ghost_cooldown
        return self.prize
