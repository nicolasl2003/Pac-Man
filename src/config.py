import json
import os
import sys
from enum import Enum
from typing import Self, Any

from pydantic import BaseModel, Field, ValidationError


class ConfigError(Exception):
    """Config errors Exception class."""
    pass


class ConfigWrapper:
    """The configuration of PacMan.

    framerate -- The target frames per seconds
    ticks_per_sec -- The number of ticks per seconds
    highscore_filename -- The path of the highscore data file
    name_length -- The longest name the highscores keep
    screen_width -- The width of the game window
    screen_height -- The height of the game window
    lives -- The number of lives the player has
    pacgum_count -- The number of pacgum per level, -1 for every free cell
    super_pacgum_count -- The number of super pacgum per level
    pacgum_points -- The number of points a pacgum awards
    ss_pacgum_points -- The number of points a super pacgum awards
    ghost_points -- The number of points killing a ghost gives
    seed -- The forced seed of the level
    level_time -- The seconds you get to complete de level
    ghost_count -- The number of ghosts per level
    ghost_cooldown -- How many seconds an eaten ghost waits to respawn
    ghost_edible_cooldown -- How many seconds a ghost stays frightened
    ghost_chase -- How hard the ghosts chase the player
    """

    class ConfigModel(BaseModel):
        """The data configuration of PacMan.

        framerate -- The target frames per seconds
        ticks_per_sec -- The number of ticks per seconds
        highscore_filename -- The path of the highscore data file
        name_length -- The longest name the highscores keep
        screen_width -- The width of the game window
        screen_height -- The height of the game window
        lives -- The number of lives the player has
        pacgum_count -- The number of pacgum per level, -1 for every free cell
        super_pacgum_count -- The number of super pacgum per level
        pacgum_points -- The number of points a pacgum awards
        ss_pacgum_points -- The number of points a super pacgum awards
        ghost_points -- The number of points killing a ghost gives
        seed -- The forced seed of the level
        level_time -- The seconds you get to complete de level
        ghost_count -- The number of ghosts per level
        ghost_cooldown -- How many seconds an eaten ghost waits to respawn
        ghost_edible_cooldown -- How many seconds a ghost stays frightened
        ghost_chase -- How hard the ghosts chase the player
        """

        class GhostSpawnType(Enum):
            """The cells where the ghosts spawn.

            CORNERS -- The four corners of the maze
            CLOSED_CELL -- The cells walled on all four sides
            """

            CORNERS = "corners"
            CLOSED_CELL = "closed_cell"

        class GhostChaseType(Enum):
            """The ghost chase difficulty.

            RANDOM -- The ghosts wander randomly
            NORMAL -- The ghosts aim for the player three moves ahead
            HARDCORE -- The ghosts follow the shortest path to the player
            """

            RANDOM = "Random"
            NORMAL = "Normal"
            HARDCORE = "Hardcore"

        framerate: int = Field(default=60, ge=1, le=1000)
        ticks_per_sec: int = Field(default=4, ge=1, le=1000)
        highscore_filename: str = Field(default="highscores.json")
        name_length: int = Field(default=10, ge=1, le=10)
        screen_width: int = Field(default=700, ge=1)
        screen_height: int = Field(default=750, ge=1)
        lives: int = Field(default=3, ge=1)
        pacgum_count: int = Field(default=-1, ge=-1)
        super_pacgum_count: int = Field(default=4, ge=0)
        pacgum_points: int = Field(default=1, ge=0)
        ss_pacgum_points: int = Field(default=15, ge=0)
        ghost_points: int = Field(default=20, ge=0)
        seed: int = Field(default=42)
        level_time: int = Field(default=90, ge=1)
        ghost_count: int = Field(default=4, ge=0)
        ghost_spawn: GhostSpawnType = Field(default=GhostSpawnType.CORNERS)
        ghost_cooldown: int = Field(default=5, ge=0)
        ghost_edible_cooldown: int = Field(default=7, ge=0)
        ghost_chase: GhostChaseType = Field(default=GhostChaseType.NORMAL)

        def _dump_to_file(self, path: str) -> None:
            """Writes the default configuration, so the next run can edit it.

            path -- The path of the file to write
            """

            try:
                with open(path, "w") as file:
                    json.dump(self.model_dump(mode="json"), file, indent=4)
            except (OSError, TypeError, ValueError) as e:
                print(f"[Config] could not write a default to {path}: {e}",
                      file=sys.stderr)
                return
            print(f"[Config] a default was written to {path}", file=sys.stderr)

        @classmethod
        def load_from_file(cls, path: str) -> Self:
            """Loads and parses the config file into Config.

            A path holding no file is given one with the defaults, so a
            first run leaves a template to edit. Unknown keys are
            dropped, and a missing or invalid value falls back to its
            default with a message on stderr.
            path -- The config file path

            Raises ConfigError when the file is not a readable json object
            """

            if not os.path.exists(path):
                cls()._dump_to_file(path)
            try:
                with open(path) as file:
                    text: str = file.read()
                content: str = "\n".join(
                    "" if line.lstrip().startswith("#") else line
                    for line in text.splitlines())
                data: object = ({} if text.strip() and not content.strip()
                                else json.loads(content))
                if not isinstance(data, dict):
                    raise ValueError("The config must hold a json object")
            except (OSError, ValueError) as e:
                raise ConfigError(f"could not read {path}: {e}") from None
            return cls._from_values(data)

        @classmethod
        def _from_values(cls, data: dict[str, Any]) -> Self:
            """Builds the config, every value it cannot use left to default.

            data -- The values read from the config file
            """

            try:
                config: Self = cls(**data)
            except ValidationError as error:
                for problem in error.errors():
                    print(f"[Config] {problem['loc'][0]}: {problem['msg']}",
                          file=sys.stderr)
                    data.pop(str(problem["loc"][0]), None)
                config = cls(**data)
            defaulted: list[str] = [key for key in cls.model_fields
                                    if key not in config.model_fields_set]
            if defaulted:
                print(f"[Config] defaults used for {', '.join(defaulted)}",
                      file=sys.stderr)
            return config

    GhostSpawnType = ConfigModel.GhostSpawnType
    GhostChaseType = ConfigModel.GhostChaseType

    framerate: int
    ticks_per_sec: int
    highscore_filename: str
    name_length: int
    screen_width: int
    screen_height: int
    lives: int
    pacgum_count: int
    super_pacgum_count: int
    pacgum_points: int
    ss_pacgum_points: int
    ghost_points: int
    seed: int
    level_time: int
    ghost_count: int
    ghost_spawn: ConfigModel.GhostSpawnType
    ghost_cooldown: int
    ghost_edible_cooldown: int
    ghost_chase: ConfigModel.GhostChaseType

    _instance: ConfigModel

    def __init__(self) -> None:
        """Creates the configuration holding the default values.
        """

        self._instance = ConfigWrapper.ConfigModel()

    def load_from_file(self, path: str) -> None:
        """Loads and parses the config file into Config.

        path -- The config file path
        """
        self._instance = ConfigWrapper.ConfigModel.load_from_file(path)

    @property
    def ms_per_tick(self) -> int:
        """The time it takes for the game to tick."""
        return 1000 // self.ticks_per_sec

    def __getattr__(self, name: str) -> Any:
        """Reads a value from the loaded configuration.

        name -- The name of the configuration key

        Raises AttributeError when no such key exists
        """

        return getattr(self._instance, name)


Config: ConfigWrapper = ConfigWrapper()
