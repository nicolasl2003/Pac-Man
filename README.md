*This project has been created as part of the 42 curriculum by nilinott, fmaudhui*

# Pac-Man

## Description

Pac-Man is a Python recreation of the 1980 Namco arcade game. The player controls Pac-Man in a maze, eats pacgums to score points, and avoids four ghosts. Super pacgums placed in the four corners make the ghosts edible for a short time.

The game has 10 levels. Each level has a new maze and a 90-second time limit. The player keeps their score and remaining lives between levels. The game ends when all levels are completed or when all lives are lost. A persistent top-10 highscore table is saved to disk.

The game is built with pygame and uses a screen-based architecture (main menu, highscores, instructions, game, pause, end screen). The maze layouts come from an external maze generator package that is included in the repository as a wheel.

## Instructions

### Requirements

- Python 3.13
- Uv 0.12

### Installation

```bash
make install
```

This runs `uv sync` and installs the dependencies, including the local `mazegenerator` wheel.

### Execution

```bash
make run
```

This runs `uv run python3 pac-man.py config.json`. The program takes exactly one argument, the path to a JSON configuration file. If the file does not exist, a default configuration is written to that path.

```bash
uv run python3 pac-man.py config.json
```

### Exportation


```bash
make build
```

This runs `uv run python3 pyinstaller pac-man.py`. Which creates a binary in dist/pac-man.

```bash
uv run python3 pyinstaller pac-man.py 
```

### Other make targets

| Target       | Action                                                        |
|--------------|---------------------------------------------------------------|
| `make debug` | Runs the game under pudb (`uv run python3 -m pudb pac-man.py config.json`) |
| `make lint`  | Runs flake8 and mypy with the flags from the subject          |
| `make lint-strict` | Runs `lint` with mypy `--strict`                        |
| `make clean` | Removes `__pycache__` and `.mypy_cache` directories           |
| `make fclean`| Removes the `.venv` directory                                  |

### Controls

| Action            | Keys                          |
|-------------------|-------------------------------|
| Move up           | Arrow Up, W, Z                |
| Move down         | Arrow Down, S                 |
| Move left         | Arrow Left, A, Q              |
| Move right        | Arrow Right, D                |
| Pause / resume    | ESC or P                      |
| Cheat: skip level | N (cheat mode must be enabled first) |

ESC returns to the previous menu or pauses the game.

### Cheat mode

Cheat mode is for peer review. Enter the Konami code during a game (UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, B, A) to toggle it. While it is on:

- the player can eat ghosts whatever their state,
- the player can eat any pacgum or super pacgum,
- N skips the current level,
- the life icons change to the cheat icon.

## Configuration

The game is configured with a JSON file passed on the command line. Lines whose first non-blank character is `#` are treated as comments and ignored. Inline comments are not supported.

Unknown keys are ignored. Invalid values (wrong type or out of range) print a message on stderr and the key falls back to its default. A missing file is created with the default values. A file that is not a JSON object stops the program with a clear error message.

### Keys and defaults

| Key                       | Type    | Default       | Constraints / meaning                                              |
|---------------------------|---------|---------------|--------------------------------------------------------------------|
| `highscore_filename`      | string  | `"highscores.json"` | File where highscores are stored (relative to the working directory). |
| `screen_width`            | integer | `700`         | Window width, >= 1.                                                |
| `screen_height`           | integer | `750`         | Window height, >= 1.                                               |
| `framerate`               | integer | `60`          | Render frames per second, 1 to 1000.                               |
| `ticks_per_sec`           | integer | `4`           | Game ticks per second, 1 to 1000. Game tick = `1000 // ticks_per_sec` ms. |
| `lives`                   | integer | `3`           | Starting lives, >= 1.                                              |
| `pacgum_count`            | integer | `-1`          | Number of pacgums, >= -1. `-1` places a pacgum on every free cell. |
| `super_pacgum_count`      | integer | `4`           | Number of super pacgums, >= 0.                                     |
| `pacgum_points`           | integer | `1`           | Points for a pacgum, >= 0.                                         |
| `ss_pacgum_points`        | integer | `15`          | Points for a super pacgum, >= 0.                                   |
| `ghost_points`            | integer | `20`          | Points for eating an edible ghost, >= 0.                           |
| `ghost_count`             | integer | `4`           | Number of ghosts, >= 0.                                            |
| `ghost_spawn`             | string  | `"corners"`   | `"corners"` or `"closed_cell"`.                                    |
| `ghost_chase`             | string  | `"Normal"`    | `"Random"`, `"Normal"` or `"Hardcore"` (case-sensitive).           |
| `ghost_cooldown`          | number  | `5`           | Seconds before an eaten ghost respawns, >= 0.                      |
| `ghost_edible_cooldown`   | number  | `7`           | Seconds a ghost stays edible after a super pacgum, >= 0.           |
| `level_time`              | integer | `90`          | Time limit per level in seconds, >= 1.                             |
| `seed`                    | integer | `42`          | Seed for the first maze and for gameplay randomness.               |
| `name_length`             | integer | `10`          | Maximum length of a player name, 1 to 10.                          |

### Example

```jsonc
# config.json
{
  "highscore_filename": "highscores.json",
  "lives": 3,
  "pacgum_count": 40,
  "super_pacgum_count": 4,
  "ghost_count": 4,
  "level_time": 90,
  "seed": 42
}
```
## Highscore

Highscores are stored in a JSON file (`highscores.json` by default) as a list of objects:

```json
[
    {"name": "NICOLAS", "score": 47},
    {"name": "BONJOUR", "score": 53}
]
```

How it works:

- **Loading**: the file is read when the game state is reset, which happens at startup and when returning to the main menu. A missing file, invalid JSON, or a wrong structure gives an empty list instead of a crash.
- **Saving**: when a game ends (win or lose), the player types a name and presses ENTER. The entry is appended, the list is sorted by score in descending order and truncated to 10 entries, then written back with indentation.
- **Names**: only ASCII letters, digits and spaces are kept. The name is cut to `name_length` characters (10 by default). An empty name is replaced by `PLAYER`.
- **Scores**: negative scores are rejected, both when saving and when loading.
- **Display**: the main menu's HIGHSCORES screen lists the top 10 entries.

Why this design: a JSON file needs no database or extra dependency, and it is easy to inspect and edit by hand. The file is re-read and re-sorted on each save, so a corrupted or hand-edited file is repaired on the next write.

Known limitation: a write error (for example, a read-only directory) is not caught in the save path and ends the program with an error message.

## Maze Generation

Mazes are generated by the `mazegenerator` package version 2.1.0, MIT licensed, provided as a wheel in `mazegenerator/`. It is referenced in `pyproject.toml` by path and is used as-is, without modification. The project does not contain its own generator.

The game calls:

```python
from mazegenerator import MazeGenerator

MazeGenerator(perfect=False, seed=seed).maze
```

- `perfect=False` produces the Pac-Man style corridors (loops allowed, no strict tree).
- The first level uses `seed` from the configuration (42 by default), so it is always the same.
- Each following level uses the seed `int(f"{seed}{level}")`, for example 422, 423, ... with the default seed. The layouts are therefore deterministic for a given configuration.
- The generator is called with its default size (15 x 15).
- Any exception from the generator, or an empty grid, is wrapped in a `GeneratorError` with a readable message.

## Implementation

- **Language and libraries**: Python 3.13, pygame 2.6.1 for rendering, input and sound, pydantic 2.13.5 for configuration validation, mazegenerator 2.1.0 for mazes.
- **Configuration**: `src/config.py` strips comment lines, parses the JSON, and validates it with a pydantic model. Each invalid key is reported and reset to its default. The loaded configuration is exposed through a single `Config` object.
- **Game loop**: the game runs at a fixed number of ticks per second, separate from the render framerate. Each game tick moves the player and the ghosts one cell.
- **Player**: the last pressed direction is buffered and applied on the next tick if the corridor is free.
- **Ghosts**: four ghosts with different targeting behaviours in `Normal` mode (one follows the planner, one moves semi-randomly, one ambushes ahead of the player). Eating a super pacgum makes ghosts edible, and they flee for `ghost_edible_cooldown` seconds. An eaten ghost returns to its spawn point after `ghost_cooldown` seconds.
- **Lives**: when a ghost touches the player, the player loses a life and the player and ghosts return to their starting positions.
- **Levels**: the level is won when all pacgums are eaten. Level 10 completed leads to the end screen as a win.
- **Errors**: configuration, asset and generator errors are caught in `src/__main__.py` and printed as messages with an exit status, without a traceback.
- **Assets**: images and sounds are loaded from `src/img/` and `src/sounds/`. Missing assets raise a clear `AssetError`.

## General Software Architecture

```
pac-man.py                  entry point, calls src.__main__.run()
src/
  __main__.py               argument parsing, main loop, error handling
  config.py                 comment stripping, pydantic model, Config singleton
  errors.py                 ConfigError, AssetError, GeneratorError
  game_state.py             GameState: score, lives, level, maze building, highscore
  level.py                  Level: maze, pacgums, player, ghosts, spawn logic
  maze.py                   Maze: grid, walls, corner and spawn computation
  entities.py               ghosts, pacgums and super pacgums
  player.py                 Player: movement and eating
  scores.py                 highscore load and save
  maze_render.py            unused module (not imported by the game)
  screens/
    main_menu.py            START, HIGHSCORES, INSTRUCTIONS, QUIT
    game.py                 game screen, HUD, controls, cheat code
    pause.py                RESUME, MAIN MENU
    end.py                  win and lose screen, name entry
    highscores.py           highscore table
    instruction.py          controls and rules
manage_screen/
  screen.py                 abstract Screen base class
  renderer.py               PygameRenderer: window, images, text, input events
  button.py                 Button widget
  sound.py                  SoundManager
mazegenerator/              vendored maze generator wheel and stub
```

Relationships:

- `GameState` owns the current `Level` and the score. `Level` owns the `Maze`, the `Player` and the ghosts.
- `manage_screen/` provides the abstract `Screen` class (`on_enter`, `handle_events`, `update`, `draw`), the renderer, buttons and sound. The screens in `src/screens/` are built on top of this layer.
- `scores.py` is used by `GameState` (initial highscore) and by the end screen (saving).
- `Config` is read by `GameState`, `Level`, `entities.py` and the screens.

## Project Management

The project is tracked with [git](https://github.com/nicolasl2003/Pac-Man), with feature branches merged through pull requests and descriptive commit messages. The dedicated project management folder required by the subject is not included in this repository yet.

## Resources

### References

- [Pac-Man on Wikipedia](https://en.wikipedia.org/wiki/Pac-Man): history and rules of the original game.
- [pygame documentation](https://www.pygame.org/docs/): rendering, events, sound and sprites.

### Use of AI

AI was used occasionally and only as a helper: explaining concepts, debugging specific errors, reviewing parts of the code and helping on unit tests. We reviewed and understood every change before committing it. The game design, the architecture, and the final implementation were written and checked by us.
