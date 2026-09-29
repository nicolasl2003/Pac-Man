from enum import Enum

from pydantic import BaseModel, Field
from time import clock_gettime_ns, CLOCK_MONOTONIC
import json


class ConfigError(Exception):
    """Config errors Exception class."""
    pass


class ConfigModel(BaseModel):
    """The configuration of PacMan.

    highscore_filename -- The path of the highscore data file
    screen_width -- The width of the game window
    screen_height -- The height of the game window
    lives -- The number of lives the player has
    pacgum -- The number of pacgum per level
    super_pacgum -- The number of super pacgum per level
    pacgum_points -- The number of points a pacgum awards
    ss_pacgum_points -- The number of points a super pacgum awards
    ghost_points -- The number of points killing a ghost gives
    seed -- The forced seed of the level
    level_timer -- The time you get to complete de level
    ghost_count -- The number of ghosts per level
    """

    class GhostSpawnType(Enum):
        CORNERS = "corners"
        CLOSED_CELL = "closed_cell"

    highscore_filename: str = Field(default="highscores.json")
    screen_width: int = Field(default=700, ge=1)
    screen_height: int = Field(default=420, ge=1)
    lives: int = Field(default=3, ge=1)
    pacgum: int = Field(default=40, ge=0)
    super_pacgum: int = Field(default=4, ge=0)
    pacgum_points: int = Field(default=1)
    ss_pacgum_points: int = Field(default=15)
    ghost_points: int = Field(default=20)
    seed: int = Field(default=clock_gettime_ns(CLOCK_MONOTONIC))
    level_timer: int = Field(default=15, ge=1)
    ghost_count: int = Field(default=4, ge=0)
    ghost_spawn: GhostSpawnType = Field(default=GhostSpawnType.CORNERS)

    @staticmethod
    def load_from_file(path: str) -> None:
        """Loads and parses the config file into Config.

        path -- The config file path
        """
        try:
            with open(path) as file:
                global Config
                Config = ConfigModel(**json.load(file))
        except (IOError, json.JSONDecodeError,
                UnicodeDecodeError, FileNotFoundError) as e:
            raise ConfigError(f"Could not load the config file: {e}")
        except (ValueError, TypeError) as e:
            raise ConfigError("Misstyped json argument"
                              f" - Unsupported type or value {e}")


# The global variable instance of config
Config: ConfigModel = ConfigModel()
