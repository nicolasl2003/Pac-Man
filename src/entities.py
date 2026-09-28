from . import Cell, Maze, Direction
from enum import Enum, auto
from typings import Self


class MovingEntity:
    """A generic entity class that stores common code for entities.

    spawn -- The cell used on respawn
    cell -- The cell the entity stands on
    direction -- The current direction
    position -- The graphical position of the entity
    """

    spawn: Cell
    cell: Cell
    direction: Direction
    position: tuple[int, int]

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
        self.direction = Direction.STILL

    def move(self, maze: Maze, direction: Direction) -> bool:
        """Crosses cell toward a direction.

        Raises EntityBlockedError if a wall stops the entity
        """
        raise NotImplementedError  # TODO

    def update(self, delta_time: float) -> bool:
        """Updates the visual of the entity.

        delta_time -- The time elapsed inbetween two frames
        """
        raise NotImplementedError  # TODO

    def collides(self, other: Self) -> bool:
        """Return whether both entities share a cell."""
        return bool(self.cell == other.cell)


class Ghost(MovingEntity):
    """Ghost starting from a maze corner.

    mode -- The current behaviour of the ghost
    respawn_cooldown -- The amount of time left before the ghost respawns
    edible_cooldown -- The cooldown for which the ghost is edible
    """

    mode: Self.GhostMode
    respawn_cooldown: int
    edible_cooldown: int

    class GhostMode(Enum):
        """The ghost behaviours.

        CHASE -- Chase mode
        EDIBLE -- Edible mode
        """

        CHASE = auto()
        EDIBLE = auto()
        DEAD = auto()

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
