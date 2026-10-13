from entities import EdibleEntity
from . import Direction, Ghost, Cell, Entity, MovingEntity, GameState


class Player(MovingEntity):
    """The PacMan controlled by the player."""

    def __init__(self, spawn: Cell) -> None:
        """Creates the player.

        spawn -- The cell on which to spawn the player
        """
        super().__init__(spawn)

    def tick(self) -> None:
        raise NotImplementedError  # TODO

    def get_collisions(self) -> list[Entity]:
        """Lists all the collisions of the player."""

        return [entity
                for entity in self.cell.entities
                if entity is not self and self.collides(entity)
                ]

    def move(self, direction: Direction) -> None:
        """Moves one cell towards a direction.

        direction -- The direction you move the entity
        """

        super().move(direction)

        for collision in self.get_collisions():
            if isinstance(collision, EdibleEntity) and collision.edible:
                collision.eat()
            elif isinstance(collision, Ghost):
                GameState.level.lose_life()

    def update(self, delta_time: int) -> None:
        """Updates the visual of the player.

        delta_time -- The time elapsed inbetween two frames
        """

        super().update(delta_time)
