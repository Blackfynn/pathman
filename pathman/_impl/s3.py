import os
import importlib
from typing import List, Generator
from pathlib import PurePath

from pathman.base import AbstractPath, RemotePath
from pathman.utils import is_file


class S3Path(AbstractPath, RemotePath):
    """ Wrapper around `s3fs.S3FileSystem`  """

    def __init__(self, path: str, **kwargs) -> None:
        try:
            importlib.import_module("s3fs")
        except ImportError:
            raise ImportError("s3fs is required for S3Path")

        from s3fs import S3FileSystem  # type: ignore

        self._original_kwargs = dict({}, **kwargs)
        self._pathstr = path
        if "anon" not in kwargs:
            kwargs["anon"] = False
        self._anon = kwargs["anon"]
        self._path = S3FileSystem(**kwargs)

    def __str__(self) -> str:
        return self._pathstr

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        return self._pathstr == other._pathstr

    def __truediv__(self, key) -> "S3Path":
        return self.join(key)

    @property
    def extension(self):
        return os.path.splitext(self._pathstr)[1]

    @property
    def bucket(self):
        return str(self._pathstr).replace("s3://", "").split("/")[0]

    @property
    def key(self):
        tokens = str(self._pathstr).replace("s3://", "").split("/")
        return "/".join(tokens[1:])

    def exists(self) -> bool:
        return self._path.exists(self._pathstr)

    def touch(self) -> None:
        return self._path.touch(self._pathstr)

    def is_dir(self) -> bool:
        return self.exists() and not is_file(self._pathstr)

    def is_file(self) -> bool:
        return self.exists() and is_file(self._pathstr)

    def mkdir(self, **kwargs) -> None:
        return self._path.mkdir(self._pathstr, **kwargs)

    def rmdir(self, recursive=False, **kwargs) -> None:
        if recursive:
            return self._path.rm(self._pathstr, recursive=True, **kwargs)
        return self._path.rmdir(self._pathstr, **kwargs)

    def join(self, *pathsegments: str) -> "S3Path":
        joined = os.path.join(self._pathstr, *pathsegments)
        return S3Path(joined, **self._original_kwargs)

    def open(self, mode="r", **kwargs):
        return self._path.open(self._pathstr, mode=mode, **kwargs)

    def write_bytes(self, contents, **kwargs):
        with self.open("wb") as f:
            written = f.write(contents)
        return written

    def write_text(self, contents, **kwargs):
        with self.open("w") as f:
            written = f.write(contents)
        return written

    def remove(self) -> None:
        return self._path.rm(self._pathstr)

    def read_text(self, **kwargs):
        with self.open("r") as f:
            contents = f.read(**kwargs)
        return contents

    def read_bytes(self, **kwargs):
        with self.open("rb") as f:
            contents = f.read(**kwargs)
        return contents

    def expanduser(self) -> "S3Path":
        return self

    def abspath(self) -> "S3Path":
        return self

    def walk(self, **kwargs) -> Generator["S3Path", None, None]:
        for root, directories, files in self._path.walk(self._pathstr, **kwargs):
            for f in files:
                yield S3Path(os.path.join(root, f), **self._original_kwargs)

    def ls(self, refresh=True) -> List["S3Path"]:
        all_files = [
            S3Path("s3://" + c, **self._original_kwargs)
            for c in self._path.ls(self._pathstr)
        ]
        return all_files

    def glob(self, pattern) -> List["S3Path"]:
        globber = self.join(pattern)._pathstr
        return [
            S3Path("s3://" + p, **self._original_kwargs)
            for p in self._path.glob(globber)
        ]

    def with_suffix(self, suffix) -> "S3Path":
        return S3Path(self._pathstr + suffix, **self._original_kwargs)

    @property
    def stem(self) -> str:
        return PurePath(self._pathstr).stem

    @property
    def parts(self) -> List[str]:
        tokens = self._pathstr.split("/")
        tokens = [t for t in tokens if t not in [""]]
        return tokens
