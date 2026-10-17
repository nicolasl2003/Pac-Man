"""Reports the pygame API the game uses, and refuses the forbidden ones.

The project may only call pygame functions that have an equivalent in the
MiniLibX. This script imports the package, resolves the pygame objects its
modules hold by identity, then walks their compiled code to collect the
attribute chains rooted on those objects. Nothing is read as text.
"""

import dis
import importlib
import sys
import types
from pathlib import Path
from typing import Iterator

# Calls with a MiniLibX equivalent. A trailing dot allows a whole subtree.
ALLOWED: frozenset[str] = frozenset({
    "pygame.init",
    "pygame.quit",
    "pygame.error",
    "pygame.version.",
    "pygame.display.init",
    "pygame.display.quit",
    "pygame.display.get_init",
    "pygame.display.set_mode",
    "pygame.display.set_caption",
    "pygame.display.get_surface",
    "pygame.display.flip",
    "pygame.Surface",
    "pygame.event.get",
    "pygame.QUIT",
    "pygame.KEYDOWN",
    "pygame.KEYUP",
    "pygame.K_",
    "pygame.MOUSEBUTTONDOWN",
    "pygame.MOUSEBUTTONUP",
    "pygame.MOUSEMOTION",
    "pygame.font.init",
    "pygame.font.quit",
    "pygame.font.Font",
    "pygame.font.SysFont",
    "pygame.time.Clock",
    # Sound is not graphics: there is nothing to draw, so nothing to mirror.
    "pygame.mixer.",
    # Reading an image file is data loading (mlx_xpm_file_to_image).
    "pygame.image.load",
    # A flag constant, it draws nothing by itself.
    "pygame.SRCALPHA",
})

# Calls with no MiniLibX equivalent, or that bypass the drawing we must write.
# A name that ALLOWED also covers is accepted: the exceptions live there.
FORBIDDEN: frozenset[str] = frozenset({
    "pygame.draw.",
    "pygame.transform.",
    "pygame.image.",
    "pygame.sndarray.",
    "pygame.surfarray.",
    "pygame.sprite.",
    "pygame.mask.",
    "pygame.key.",
    "pygame.mouse.",
    "pygame.joystick.",
    "pygame.camera.",
    "pygame.midi.",
    "pygame.scrap.",
    "pygame.cursors.",
    "pygame.gfxdraw.",
    "pygame.freetype.",
    "pygame.time.wait",
    "pygame.time.delay",
    "pygame.time.set_timer",
    "pygame.display.update",
    "pygame.display.set_icon",
    "pygame.display.set_palette",
    "pygame.display.toggle_fullscreen",
    "pygame.Rect",
    "pygame.FULLSCREEN",
    "pygame.RESIZABLE",
    "pygame.SCALED",
    "pygame.NOFRAME",
    "pygame.OPENGL",
    "pygame.DOUBLEBUF",
    "pygame.TEXTINPUT",
})

# Surface methods with no MiniLibX equivalent. The object they are called on
# cannot be resolved without running the game, so they are only warned about.
SUSPECT_METHODS: frozenset[str] = frozenset({
    "convert", "set_colorkey", "set_alpha",
    "subsurface", "blits", "scroll", "set_clip", "unicode",
})

# Surface methods accepted as image processing: convert_alpha and get_at only
# read or convert pixels, fill is mlx_clear_window when it paints black.
CLEAR_COLOR: tuple[int, int, int] = (0, 0, 0)


def _matches(name: str, rules: frozenset[str]) -> bool:
    """Returns whether a dotted name is covered by a rule set.

    name -- the dotted pygame name that was used
    rules -- exact names, or prefixes ending with a dot or an underscore
    """

    for rule in rules:
        if name == rule:
            return True
        if rule.endswith((".", "_")) and name.startswith(rule):
            return True
    return False


def _belongs_to_pygame(value: object) -> bool:
    """Returns whether an object pygame exposes is pygame's own.

    A module pygame re-exports, such as the sys it imports, keeps its own
    name: taken as a root it would rename every stdlib call of the game.
    """

    owner = getattr(value, "__name__" if isinstance(value, types.ModuleType)
                    else "__module__", None)
    return isinstance(owner, str) and owner.split(".")[0] == "pygame"


def _pygame_paths() -> tuple[dict[int, str], set[str]]:
    """Returns the pygame objects usable as roots, and every pygame name.

    Only modules, classes and callables are keyed by id: a constant such as
    pygame.KEYDOWN shares its identity with any equal value in the game, so
    it is reached through its owning module instead.
    """

    roots: dict[int, str] = {}
    known: set[str] = set()
    pygame = sys.modules.get("pygame")
    if pygame is None:
        return roots, known
    modules = [pygame] + [module for name, module in sys.modules.items()
                          if name.startswith("pygame.")
                          and isinstance(module, types.ModuleType)]
    for module in modules:
        roots.setdefault(id(module), module.__name__)
        known.add(module.__name__)
    for module in modules:
        for attribute in dir(module):
            if attribute.startswith("__"):
                continue
            try:
                value = getattr(module, attribute)
            except Exception:
                continue
            name = f"{module.__name__}.{attribute}"
            known.add(name)
            if not _belongs_to_pygame(value):
                continue
            if isinstance(value, (types.ModuleType, type)) or callable(value):
                roots.setdefault(id(value), name)
    return roots, known


def _package_modules(package: str) -> list[types.ModuleType]:
    """Returns the imported modules of a package, the package included."""

    return [module for name, module in sorted(sys.modules.items())
            if (name == package or name.startswith(package + "."))
            and isinstance(module, types.ModuleType)]


def _module_code(module: types.ModuleType) -> types.CodeType | None:
    """Returns the compiled code of a module, or None when unavailable."""

    loader = getattr(module, "__loader__", None)
    getter = getattr(loader, "get_code", None)
    if getter is None:
        return None
    try:
        code = getter(module.__name__)
    except (ImportError, OSError, TypeError, ValueError):
        return None
    return code if isinstance(code, types.CodeType) else None


def _code_objects(code: types.CodeType) -> Iterator[types.CodeType]:
    """Yields a code object and every code object nested inside it."""

    yield code
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType):
            yield from _code_objects(constant)


def _chains(code: types.CodeType,
            roots: dict[str, str]) -> Iterator[tuple[str, str, int]]:
    """Yields the pygame names a code object loads.

    code -- the compiled code to walk
    roots -- global name used in the source, mapped to its pygame name
    """

    instructions = list(dis.get_instructions(code))
    for index, instruction in enumerate(instructions):
        if instruction.opname not in ("LOAD_GLOBAL", "LOAD_NAME",
                                      "LOAD_DEREF"):
            continue
        name = str(instruction.argval)
        if name not in roots:
            continue
        chain = roots[name]
        line = instruction.positions.lineno if instruction.positions else None
        for follower in instructions[index + 1:]:
            if follower.opname not in ("LOAD_ATTR", "LOAD_METHOD"):
                break
            chain = f"{chain}.{follower.argval}"
        yield chain, code.co_filename, line or code.co_firstlineno


def _roots(module: types.ModuleType,
           paths: dict[int, str]) -> dict[str, str]:
    """Returns the names of a module that hold a pygame object."""

    found: dict[str, str] = {}
    for name, value in vars(module).items():
        if name.startswith("__"):
            continue
        path = paths.get(id(value))
        if path is not None:
            found[name] = path
    return found


def _longest_known(chain: str, known: set[str]) -> str:
    """Cuts a chain back to the longest part pygame actually exposes."""

    parts = chain.split(".")
    for stop in range(len(parts), 1, -1):
        candidate = ".".join(parts[:stop])
        if candidate in known:
            return candidate
    return parts[0]


def _suspect_methods(code: types.CodeType) -> Iterator[str]:
    """Yields the Surface methods of a code object that need a check.

    A fill is only accepted with the clear colour, written as a literal.
    code -- the compiled code to walk
    """

    instructions = list(dis.get_instructions(code))
    for index, instruction in enumerate(instructions):
        attribute = str(instruction.argval)
        if instruction.opname not in ("LOAD_ATTR", "LOAD_METHOD"):
            continue
        if attribute in SUSPECT_METHODS:
            yield attribute
        elif attribute == "fill":
            following = instructions[index + 1:index + 2]
            if not (following and following[0].opname == "LOAD_CONST"
                    and following[0].argval == CLEAR_COLOR):
                yield "fill"


def _annotate(level: str, path: str, line: int, message: str) -> None:
    """Prints one GitHub annotation on stdout."""

    print(f"::{level} file={path},line={line}::{message}")


def audit(package: str) -> int:
    """Audits a package and returns the process exit code.

    package -- the importable name of the game package
    Returns 1 when a forbidden call was found, 0 otherwise
    """

    sys.path.insert(0, str(Path.cwd()))
    importlib.import_module(package)
    try:
        # The package may only reach pygame through its entry point
        importlib.import_module(f"{package}.__main__")
    except ImportError:
        pass
    paths, known = _pygame_paths()
    if not paths:
        print(f"{package}: pygame is not imported, nothing to audit")
        return 0
    errors = 0
    warnings = 0
    seen: set[tuple[str, str, int]] = set()
    for module in _package_modules(package):
        code = _module_code(module)
        if code is None:
            continue
        roots = _roots(module, paths)
        for block in _code_objects(code):
            for chain, filename, line in _chains(block, roots):
                name = _longest_known(chain, known)
                key = (name, filename, line)
                if key in seen:
                    continue
                seen.add(key)
                where = str(Path(filename).resolve())
                if _matches(name, ALLOWED):
                    continue
                if _matches(name, FORBIDDEN):
                    _annotate("error", where, line,
                              f"{name} has no MiniLibX equivalent")
                    errors += 1
                else:
                    _annotate("warning", where, line,
                              f"{name} is not on the allowed list, check it"
                              " against the MiniLibX before shipping")
                    warnings += 1
            for attribute in _suspect_methods(block):
                key = (attribute, block.co_filename, block.co_firstlineno)
                if key in seen:
                    continue
                seen.add(key)
                _annotate("warning",
                          str(Path(block.co_filename).resolve()),
                          block.co_firstlineno,
                          f".{attribute}() is a pygame Surface method with no"
                          " MiniLibX equivalent; confirm the object it is"
                          " called on")
                warnings += 1
    print(f"{package}: {errors} forbidden call(s), {warnings} to check")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(audit(sys.argv[1] if len(sys.argv) > 1 else "src"))
