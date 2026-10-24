class CellNotFoundError(Exception):
    """Error when a cell is not part of the maze."""

    def __init__(self, first: tuple[int, int] | str) -> None:
        """Creates the error.

        first -- The coordinates or name of the cell
        """

        if isinstance(first, tuple):
            super().__init__(f"Cell at {first} is not part of the maze")
        else:
            super().__init__(f"Cell {first} not found")


class GeneratorError(Exception):
    """Error when the assigned maze generator gives no usable maze."""

    pass
