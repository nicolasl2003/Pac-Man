from pydantic import BaseModel, Field
import json


class ConfigError(Exception):
    pass


class ConfigModel(BaseModel):

    highscore_filename: str = Field(default="highscores.json")
    screen_width: int = Field(default=700)
    screen_height: int = Field(default=420)
    lives: int = Field(default=3)
    pacgum: int = Field(default=40)
    super_pacgum: int = Field(default=4)
    pacgum_points: int = Field(default=1)
    ss_pacgum_points: int = Field(default=15)
    ghost_points: int = Field(default=20)
    seed: int = Field(default=69)
    level_timer: int = Field(default=15)
    ghost_count: int = Field(default=4)

    @staticmethod
    def load_from_file(path: str) -> None:
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


Config: ConfigModel = ConfigModel()
