from . import Direction, Cell, Entity, MovingEntity


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
        self.move(self.next_direction)

    def get_collisions(self) -> list[Entity]:
        """Lists all the collisions of the player."""

        return [entity
                for entity in self.cell.entities
                if entity is not self and self.collides(entity)
                ]

    def move(self, direction: Direction) -> None:
        """Moves one cell towards a direction.

        Checks collision before and after move to properly get rid of ghosts

        direction -- The direction you move the entity
        """

        from src import GameState, EdibleEntity, Ghost

        def _collide() -> None:

            for collision in self.get_collisions():
                if isinstance(collision, EdibleEntity) and collision.edible:
                    collision.eat()
                elif isinstance(collision, Ghost):
                    GameState.level.lose_life()

        _collide()
        super().move(direction)
        _collide()

    def update(self, delta_time: int) -> None:
        """Updates the visual of the player.

        delta_time -- The time elapsed inbetween two frames
        """

        super().update(delta_time)
