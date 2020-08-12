import os
import shutil
from pathlib import Path as PathLibPath
from typing import List, Generator

from pathman.base import AbstractPath


class LocalPath(AbstractPath):
    """ Wrapper around `pathlib.Path` """

    def __init__(self, path: str, **kwargs) -> None:
        self._path = PathLibPath(path)
        self._pathstr = path

    def __str__(self) -> str:
        return self._pathstr

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        return self._pathstr == other._pathstr

    def __truediv__(self, key) -> "LocalPath":
        return self.join(key)

    @property
    def extension(self) -> str:
        return self._path.suffix

    def exists(self) -> bool:
        return self._path.exists()

    def touch(self) -> None:
        return self._path.touch()

    def is_dir(self) -> bool:
        return self._path.is_dir()

    def is_file(self) -> bool:
        return self._path.is_file()

    def mkdir(self, **kwargs) -> None:
        return self._path.mkdir(**kwargs)

    def rmdir(self, recursive=False) -> None:
        if recursive:
            return shutil.rmtree(self._pathstr)
        return self._path.rmdir()

    def join(self, *pathsegments: str) -> "LocalPath":
        return LocalPath(str(self._path.joinpath(*pathsegments)))

    def open(self, mode="r", **kwargs):
        return self._path.open(mode=mode, **kwargs)

    def write_bytes(self, contents, **kwargs):
        return self._path.write_bytes(contents, **kwargs)

    def write_text(self, contents, **kwargs):
        return self._path.write_text(contents, **kwargs)

    def remove(self) -> None:
        self._path.unlink()

    def read_text(self, **kwargs):
        return self._path.read_text(**kwargs)

    def read_bytes(self, **kwargs):
        return self._path.read_bytes(**kwargs)

    def expanduser(self) -> "LocalPath":
        return LocalPath(str(self._path.expanduser()))

    def abspath(self) -> "LocalPath":
        return LocalPath(str(self._path.resolve()))

    def walk(self, **kwargs) -> Generator["LocalPath", None, None]:
        for root, directories, files in os.walk(self._pathstr, **kwargs):
            for f in files:
                yield LocalPath(os.path.join(root, f))

    def ls(self) -> List["LocalPath"]:
        return [LocalPath(str(p)) for p in self._path.iterdir()]

    def glob(self, path) -> List["LocalPath"]:
        return [LocalPath(str(p)) for p in self._path.glob(path)]

    def with_suffix(self, suffix) -> "LocalPath":
        return LocalPath(str(self._path.with_suffix(suffix)))

    @property
    def stem(self) -> str:
        return self._path.stem

    @property
    def parts(self) -> List[str]:
        return list(self._path.parts)
