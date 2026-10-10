from . import Cell, Entity, MovingEntity, Direction


class Player(MovingEntity):
    """The PacMan controlled by the player."""

    def __init__(self, spawn: Cell) -> None:
        """Creates the player.

        spawn -- The cell on which to spawn the player
        """
        super().__init__(spawn)
        self.next_direction: Direction = self.direction

    def set_direction(self, direction: Direction) -> None:
        self.next_direction = direction

    def tick(self) -> None:
        if (self.next_direction != Direction.STILL and
           self.cell.can_move(self.next_direction)):
            self.direction = self.next_direction

        if (not self.cell.can_move(self.direction)):
            self.direction = Direction.STILL
            return

        self.move(self.direction)

    def get_collisions(self) -> list[Entity]:
        """Lists all the collisions of the player."""

        return [entity
                for entity in self.cell.entities
                if self.collides(entity)
                ]

    def update(self, delta_time: int) -> None:
        """Updates the visual of the player.

        delta_time -- The time elapsed inbetween two frames
        """

        super().update(delta_time)
