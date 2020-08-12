""" Module for abstracting over local/remote file paths """
import os
from typing import List, Union, Generator

from pathman.exc import UnsupportedPathTypeException
from pathman.base import AbstractPath
from pathman.utils import is_file
from pathman._impl import S3Path, LocalPath


class Path(AbstractPath, os.PathLike):
    """ Represents a generic path object """

    location_class_map = {"local": LocalPath, "s3": S3Path}

    def __init__(self, path: str, **kwargs) -> None:
        """Constructor for a new Path

        Parameters
        ----------
        path: str or path-like object
           A path string
        """
        path = str(path)
        self._pathstr: str = path
        self._isfile: bool = is_file(path)
        self._location: str = determine_output_location(path)
        if self._location not in self.location_class_map:
            raise UnsupportedPathTypeException("inferred location is not supported")
        self._impl: Union[AbstractPath, LocalPath, S3Path] = self.location_class_map[
            self._location
        ](  # type: ignore
            path, **kwargs
        )

    def __fspath__(self) -> str:
        return self._pathstr

    def __str__(self) -> str:
        return self._pathstr

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        return self._pathstr == other._pathstr

    def __truediv__(self, key) -> "Path":
        return Path(self._impl.__truediv__(key)._pathstr)

    @property
    def extension(self) -> str:
        """ Get the extension if the path is a file """
        return self._impl.extension

    def exists(self) -> bool:
        """ Checks if the path exists """
        return self._impl.exists()

    def touch(self) -> None:
        """ Create a file at the current path """
        self._impl.touch()
        return

    def is_dir(self) -> bool:
        """ Checks if the path is a directory """
        return self._impl.is_dir()

    def is_file(self) -> bool:
        """ Checks if the path is a file """
        return self._impl.is_file()

    def mkdir(self, **kwargs) -> None:
        """ Make a new directory """
        self._impl.mkdir(**kwargs)
        return

    def rmdir(self, recursive=False) -> None:
        """Remove a directory

        Parameters
        ----------
        recursive : bool, optional
            If True, remove directory and all contents recursively.
            If False, the directory must be empty

        """
        self._impl.rmdir(recursive=recursive)
        return

    def join(self, *pathsegments) -> "Path":
        """ Combine the current path with the given segments """
        return Path(self._impl.join(*pathsegments)._pathstr)

    def basename(self) -> str:
        """Return the base name of the current path

        Notes
        -----
        Behavior  mimics: `os.path.basename`
        """
        # Note: Move implementation to sub-classes if os.path.basename
        # turns out to not do the correct thing for some future system.
        # s3 and local files work as expected
        return os.path.basename(self._pathstr)

    def open(self, mode: str = "r", **kwargs):
        """Open a file similar to built-in open() function

        Parameters
        ----------
        mode: str, optional
            Mode to use when opening the file

        Returns
        -------
        file object

        """
        return self._impl.open(mode=mode, **kwargs)

    def write_bytes(self, contents, **kwargs) -> int:
        """Open file, write bytes, and close the file

        Parameters
        ----------
        contents: bytes
            Content to write to the file

        Returns
        -------
        int: number of bytes written

        """
        return self._impl.write_bytes(contents, **kwargs)

    def write_text(self, contents, **kwargs) -> int:
        """Open file, write text, and close file

        Parameters
        ----------
        contents: str
            Content to write to the file

        Returns
        -------
        int: number of characters written

        """
        return self._impl.write_text(contents, **kwargs)

    def read_bytes(self, **kwargs) -> bytes:
        """ Open file, read bytes, and close file """
        return self._impl.read_bytes(**kwargs)

    def read_text(self, **kwargs) -> str:
        """ Open file, read text, and close file """
        return self._impl.read_text(**kwargs)

    def remove(self) -> None:
        """
        Remove this file. If the path points to a directory, use rmdir
        instead
        """
        self._impl.remove()
        return

    def expanduser(self) -> "Path":
        """ Return a new path with ~ expanded """
        return Path(self._impl.expanduser()._pathstr)

    def dirname(self) -> "Path":
        """Return the directory name of the current path. Mimics the behavior
        of `os.path.dirname`
        """
        return Path(os.path.dirname(self._pathstr))

    def abspath(self) -> "Path":
        """ Make the current path absolute """
        return Path(self._impl.abspath()._pathstr)

    def walk(self, **kwargs) -> Generator["Path", None, None]:
        """Get a list of files below the current path

        Note
        ----
        This does not mirror the behavior of `os.walk`. A list of absolute
        paths are returned
        """
        return (Path(p._pathstr) for p in self._impl.walk(**kwargs))

    def ls(self) -> List["Path"]:
        return [Path(p._pathstr) for p in self._impl.ls()]

    def glob(self, path) -> List["Path"]:
        return [Path(p._pathstr) for p in self._impl.glob(path)]

    def with_suffix(self, suffix) -> "Path":
        return Path(self._impl.with_suffix(suffix)._pathstr)

    @property
    def stem(self) -> str:
        return self._impl.stem

    @property
    def parts(self) -> List[str]:
        """ Return path broken into its constituent parts """
        return self._impl.parts


def determine_output_location(abspath: str) -> str:
    """Determine output location given a path

    Parameters
    ---------
    abspath: str
        Path to inspect

    Returns
    -------
    str: String representation of the inferred output location

    Notes
    -----
    Possible output locations include:
        - s3
        - blackfynn
        - local
    """
    if abspath.startswith("s3"):
        return "s3"
    return "local"
