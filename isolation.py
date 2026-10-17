"""Keeps a broken import from failing more than the tests that need it."""

import ast
import builtins
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


class MissingName:
    """Stands in for a name a test file could not import.

    Calling it, iterating it or reading one of its attributes raises an
    ImportError giving the original cause.
    """

    def __init__(self, name: str, error: Exception) -> None:
        """Keeps the cause of the failed import.

        name -- the name the test file asked for
        error -- the exception raised while importing it
        """

        self._message: str = (f"cannot import {name}: "
                              f"{type(error).__name__}: {error}")

    def __getattr__(self, attribute: str) -> Any:
        """Raises the import error, or AttributeError for a private name.

        attribute -- the attribute read on the missing name
        """

        if attribute.startswith("_"):
            raise AttributeError(attribute)
        raise ImportError(self._message)

    def __call__(self, *args: object, **kwargs: object) -> Any:
        """Raises the import error.

        args -- the positional arguments of the call
        kwargs -- the keyword arguments of the call
        """

        raise ImportError(self._message)

    def __iter__(self) -> Iterator[Any]:
        """Raises the import error."""

        raise ImportError(self._message)


@contextmanager
def lenient_imports(folder: Path) -> Iterator[None]:
    """Replaces what the files of a folder fail to import by MissingName.

    The imports made by any other file, the game included, are left as is.
    folder -- the folder whose files import leniently
    """

    original = builtins.__import__

    def _import(name: str, globals: Mapping[str, object] | None = None,
                locals: Mapping[str, object] | None = None,
                fromlist: Sequence[str] | None = (), level: int = 0) -> Any:
        """Imports like the import statement, without ever raising.

        The parameters keep the names of builtins.__import__ it replaces.
        name -- the module to import
        globals -- the globals of the importing file
        locals -- the locals of the importing file
        fromlist -- the names listed after "import" in a from-import
        level -- the number of dots of a relative import
        Returns the module, or a stand-in whose missing names are MissingName
        """

        importer: object = (None if globals is None
                            else globals.get("__file__"))
        if (not isinstance(importer, str)
                or not Path(importer).resolve().is_relative_to(folder)):
            return original(name, globals, locals, fromlist, level)
        try:
            module: ModuleType = original(name, globals, locals, fromlist,
                                          level)
        except Exception as error:
            if not fromlist:
                return MissingName(name, error)
            return _stand_in(name, fromlist, ModuleType(name), error)
        if fromlist and not all(hasattr(module, attribute)
                                for attribute in fromlist):
            return _stand_in(name, fromlist, module, None)
        return module

    builtins.__import__ = _import
    try:
        yield
    finally:
        builtins.__import__ = original


def _stand_in(name: str, fromlist: Sequence[str], module: ModuleType,
              error: Exception | None) -> ModuleType:
    """Builds a module holding the names asked to a module.

    name -- the module the names are imported from
    fromlist -- the names to import
    module -- the imported module, empty when its import failed
    error -- the cause of the failed import, None when the module exists
    Returns a module where every name the module lacks is a MissingName
    """

    stand_in: ModuleType = ModuleType(name)
    for attribute in fromlist:
        try:
            setattr(stand_in, attribute, getattr(module, attribute))
        except AttributeError as missing:
            cause: Exception = missing if error is None else error
            setattr(stand_in, attribute,
                    MissingName(f"{name}.{attribute}", cause))
    return stand_in


class UnimportedTest(pytest.Item):
    """Fails one test of a file that could not be imported.

    Public Functions:
        runtest -- fails with the import error of the file
        reportinfo -- returns the file and name the report shows
    """

    def __init__(self, *, error: str, **kwargs: Any) -> None:
        """Keeps the import error the test fails with.

        error -- the report of the failed import
        kwargs -- the arguments pytest gives to every item
        """

        super().__init__(**kwargs)
        self._error: str = error

    def runtest(self) -> None:
        """Fails with the import error of the file."""

        pytest.fail(self._error, pytrace=False)

    def reportinfo(self) -> tuple[Path, None, str]:
        """Returns the file and name the report shows for the test."""

        return self.path, None, self.name


class IsolatedModule(pytest.Module):
    """Collects a test file so a broken import only fails the tests using it.

    A name the file cannot import becomes a MissingName, so the tests that
    use it fail while the others run. If the file still cannot be imported,
    each of its tests fails on its own instead of the whole run stopping.

    Public Functions:
        collect -- returns the tests of the file
    """

    def collect(self) -> list[pytest.Item | pytest.Collector]:
        """Returns the tests of the file, failing ones if it cannot load."""

        try:
            with lenient_imports(self.path.parent.resolve()):
                return list(super().collect())
        except Exception as error:
            report: str = f"{type(error).__name__}: {error}"
            return [UnimportedTest.from_parent(self, name=name, error=report)
                    for name in _test_names(self.path)]


def _test_names(path: Path) -> list[str]:
    """Returns the names of the test functions written in a file.

    path -- the test file to read
    """

    tree: ast.Module = ast.parse(path.read_text(), str(path))
    return [node.name for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name.startswith("test")]
