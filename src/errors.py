from . import Cell, MovingEntity


class CellNotFoundError(Exception):
    """Error when a cell is not part of the maze."""

    def __init__(self, coords: tuple[int, int]) -> None:
        """Creates the error.

        coords -- The coordinates that are not part of the maze
        """

        super().__init__("Cell at {coords} is not part of the maze")


class EntityBlockedError(Exception):
    """Error when the entity cannot move to the designated cell."""

    def __init__(self, entity: MovingEntity, cell: Cell) -> None:
        """Creates the error.

        entity -- The entity that got blocked in its move
        cell -- The cell it tried to reach
        """

        super().__init__(f"Entity {type(entity).__name__}"
                         f" cannot reach cell {cell}")
