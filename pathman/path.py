""" Module for abstracting over local/remote file paths """
import os
import boto3  # type: ignore
import shutil
import re
import requests
import logging
from typing import List, Union, no_type_check, Generator
from abc import ABC, abstractmethod, abstractproperty
from pathlib import Path as PathLibPath, PurePath
from pathman.exc import UnsupportedPathTypeException, UnsupportedCopyOperation
from s3fs import S3FileSystem  # type: ignore
from blackfynn import Blackfynn  # type: ignore
from blackfynn.models import BaseDataNode  # type: ignore
from tempfile import TemporaryDirectory


class AbstractPath(ABC):
    """ Defines the interface for all Path-like objects """

    @abstractproperty
    def extension(self):
        pass

    @abstractmethod
    def exists(self):
        pass

    @abstractmethod
    def touch(self):
        pass

    @abstractmethod
    def is_dir(self):
        pass

    @abstractmethod
    def is_file(self):
        pass

    @abstractmethod
    def mkdir(self, **kwargs):
        pass

    @abstractmethod
    def rmdir(self, recursive=False):
        pass

    @abstractmethod
    def join(self, *pathsegments: str):
        pass

    @abstractmethod
    def open(self, mode="r", **kwargs):
        pass

    @abstractmethod
    def write_bytes(self, contents, **kwargs):
        pass

    @abstractmethod
    def write_text(self, contents, **kwargs):
        pass

    @abstractmethod
    def read_bytes(self, **kwargs):
        pass

    @abstractmethod
    def read_text(self, **kwargs):
        pass

    @abstractmethod
    def remove(self):
        pass

    @abstractmethod
    def expanduser(self):
        pass

    @abstractmethod
    def abspath(self):
        pass

    @abstractmethod
    def walk(self, **kwargs):
        pass

    @abstractmethod
    def ls(self):
        pass

    @abstractmethod
    def __truediv__(self, key):
        pass

    @abstractmethod
    def glob(self, _glob):
        pass

    @abstractmethod
    def with_suffix(self, suffix):
        pass

    @abstractproperty
    def stem(self):
        pass

    @abstractproperty
    def parts(self):
        pass


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


class RemotePath(object):
    """ A mixin that represents any non-local path

    Notes
    -----
        This can be used to add additional methods to remote files
        that are specific to managing remote resources. This will
        also allow us to unify the API for managing remote resources
        across cloud providers should that be necessary in the future.
    """


class BlackfynnPath(AbstractPath, RemotePath):
    """ Representation of a path on the Blackfynn platform """

    def __init__(self, path: str, dataset=None, profile="default", **kwargs):
        if not path.startswith("bf://"):
            raise ValueError("Blackfynn paths must begin with bf://")
        if "." in path:
            self._extension = path[path.rfind(".") :]
            path = path[: path.rfind(".")]
        else:
            self._extension = ""
        if dataset is None:
            self._pathstr = path
            if len(self.parts) == 0:
                raise ValueError("Must specify a dataset")
            dataset = self.dataset
        else:
            self._pathstr = "bf://" + os.path.join(dataset, path[len("bf://") :])
        self._profile = profile
        bf = Blackfynn(self._profile)
        root = None
        try:
            root = bf.get_dataset(dataset)
        except Exception:
            # When the API doesn't find a dataset, it raises a generic
            # exception, which is what we have to catch.
            raise FileNotFoundError("Dataset {} was not found".format(dataset))
        tokens = self.parts[2:]
        for token in tokens:
            col = _get_collection_by_name(root, token)
            if col is None and token == tokens[-1]:
                root = _get_package_by_name(root, token)
            else:
                root = col
            if root is None:
                break
        self._bf_object: BaseDataNode = root

    def __str__(self) -> str:
        return self._pathstr

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        return self._pathstr == other._pathstr

    def __truediv__(self, key) -> "BlackfynnPath":
        return self.join(key)

    @property
    def extension(self) -> str:
        return self._extension

    @property
    def dataset(self) -> str:
        return self.parts[1]

    @property
    def path(self):
        return "/".join(self.parts[2:]) + self.extension

    @property
    def parts(self):
        parts = self._pathstr.split("/")
        return [part for part in parts if part not in [""]]

    @property
    def stem(self):
        return self.parts[-1]

    def exists(self) -> bool:
        return self._bf_object is not None and self._bf_object.exists

    def touch(self, exist_ok=True, **kwargs):
        if self.exists():
            if exist_ok:
                return
            else:
                raise FileExistsError("{} already exists".format(self))
        self.write_text("", use_agent=False)

    def is_dir(self) -> bool:
        return self.exists() and hasattr(self._bf_object, "upload")

    def is_file(self) -> bool:
        return self.exists() and not self.is_dir()

    def mkdir(self, parents=False, exist_ok=False, **kwargs):
        if self.exists():
            if exist_ok:
                return
            else:
                raise FileExistsError("Can't mkdir {}".format(self))

        bf = Blackfynn(self._profile)
        tokens = self.parts[1:]
        root = bf.get_dataset(tokens.pop(0))
        for token in tokens:
            prev_root = root
            root = _get_collection_by_name(root, token)
            if root is None:
                if token != tokens[-1]:  # the missing token is not at the end
                    if parents is False:
                        raise FileNotFoundError(
                            "Missing directory {dir} in {path}".format(
                                dir=token, path=self._pathstr
                            )
                        )
                    else:
                        root = prev_root.create_collection(token)
                else:
                    self._bf_object = prev_root.create_collection(token)

    def rmdir(self, **kwargs):
        if self.is_dir():
            self._bf_object.delete()

    def join(self, *pathsegments: str) -> "BlackfynnPath":
        joined = os.path.join(self._pathstr, *pathsegments)
        return BlackfynnPath(joined)

    def open(self, mode="r", **kwargs):
        raise NotImplementedError("Blackfynn paths can't be opened")

    def write_bytes(self, contents, **kwargs):
        return self._write(contents, "wb", **kwargs)

    def write_text(self, contents, **kwargs):
        return self._write(contents, "w", **kwargs)

    def read_bytes(self, **kwargs):
        return self._read().content

    def read_text(self, **kwargs):
        return self._read().text

    def remove(self):
        if self.exists():
            self._bf_object.delete()

    def expanduser(self) -> "BlackfynnPath":
        return self

    def abspath(self) -> "BlackfynnPath":
        return self

    def walk(self, **kwargs) -> Generator["BlackfynnPath", None, None]:
        if not self.is_dir():
            return
        stack = [(self._bf_object, self._pathstr)]
        while len(stack) > 0:
            root, path = stack.pop()
            for item in root.items:
                item_path = os.path.join(path, item.name)
                if "Collection" in item.type:
                    stack.append((item, item_path))
                else:
                    extension = None
                    if hasattr(item, "sources"):
                        if len(item.sources) > 1:
                            logging.warning("{} has too many sources".format(item))
                        extension = Path(item.sources[0].s3_key).extension
                    yield BlackfynnPath(item_path + (extension if extension else ""))

    def glob(self, pattern: str) -> List["BlackfynnPath"]:
        regex_text = "("
        for char in pattern:
            if char == "*":
                regex_text += "[^/]*"
            elif char == "?":
                regex_text += "."
            else:
                regex_text += re.escape(char)
        regex_text += ")"
        regex = re.compile(regex_text)
        files = self.walk()
        paths: set = set()

        for _file in files:
            match = regex.match(_file.path)
            if match:
                paths.add(match.group(0))

        return list(paths)

    def ls(self) -> List["BlackfynnPath"]:
        if not self.is_dir():
            return []
        files = []
        for item in self._bf_object.items:
            ext = None
            if hasattr(item, "sources"):
                ext = Path(item.sources[0].s3_key).extension
                if len(item.sources) > 1:
                    logging.warning("{} has too many sources".format(item))
            files.append(self.join(item.name + (ext if ext else "")))
        return files

    def with_suffix(self, suffix) -> "BlackfynnPath":
        return BlackfynnPath(self._pathstr + suffix)

    def _write(self, contents, mode, **kwargs):
        """
        Writes the specified `contents` to this BlackfynnPath. If this object
        references a directory, then nothing will be written, and this method
        will return 0. Appending to an existing file is not supported, and will
        raise an IOError.

        Parameters
        ----------
        contents:
            The contents to be written. Either bytes or a string.
        mode:
            The IO mode to use when writting. Append is not supported.
        kwargs:
            Keyword arguments passed into the blackfynn.upload command
        """
        if mode.startswith("a"):
            raise IOError("Append is not supported for Blackfynn paths")
        if self.is_dir():
            return 0
        if self.exists():
            self._bf_object.delete()
        with TemporaryDirectory() as tmp:
            path = "{dir}/{name}{ext}".format(
                dir=tmp, name=self.stem, ext=self.extension
            )
            with open(path, mode) as f:
                f.write(contents)
            parent_dir = BlackfynnPath(self._pathstr[: self._pathstr.rfind("/")])
            data = parent_dir._bf_object.upload(path, **kwargs)
            bf = Blackfynn(self._profile)
            self._bf_object = bf.get(data[0][0]["package"]["content"]["id"])

        return len(contents)

    def _read(self):
        if not self.is_file():
            return
        if len(self._bf_object.sources) > 1:
            logging.warning("{} has too many sources".format(self._bf_object))
        url = self._bf_object.sources[0].url
        response = requests.get(url)
        # If the response has an error status, raise an appropriate Exception
        response.raise_for_status()
        return response


class S3Path(AbstractPath, RemotePath):
    """ Wrapper around `s3fs.S3FileSystem`  """

    def __init__(self, path: str, **kwargs) -> None:
        self._pathstr = path
        self._path = S3FileSystem(anon=False, **kwargs)

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
        return S3Path(joined)

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
                yield S3Path(os.path.join(root, f))

    def ls(self, refresh=True) -> List["S3Path"]:
        all_files = [S3Path("s3://" + c) for c in self._path.ls(self._pathstr)]
        return all_files

    def glob(self, pattern) -> List["S3Path"]:
        globber = self.join(pattern)._pathstr
        return [S3Path("s3://" + p) for p in self._path.glob(globber)]

    def with_suffix(self, suffix) -> "S3Path":
        return S3Path(self._pathstr + suffix)

    @property
    def stem(self) -> str:
        return PurePath(self._pathstr).stem

    @property
    def parts(self) -> List[str]:
        tokens = self._pathstr.split("/")
        tokens = [t for t in tokens if t not in [""]]
        return tokens


class Path(AbstractPath, os.PathLike):
    """ Represents a generic path object """

    location_class_map = {"local": LocalPath, "s3": S3Path, "bf": BlackfynnPath}

    def __init__(self, path: str, **kwargs) -> None:
        """ Constructor for a new Path

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
        self._impl: Union[AbstractPath, LocalPath, S3Path, BlackfynnPath] = (
            self.location_class_map[self._location](  # type: ignore
                path, **kwargs
            )
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
        """ Remove a directory

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
        """ Return the base name of the current path

        Notes
        -----
        Behavior  mimics: `os.path.basename`
        """
        # Note: Move implementation to sub-classes if os.path.basename
        # turns out to not do the correct thing for some future system.
        # s3 and local files work as expected
        return os.path.basename(self._pathstr)

    def open(self, mode: str = "r", **kwargs):
        """ Open a file similar to built-in open() function

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
        """ Open file, write bytes, and close the file

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
        """ Open file, write text, and close file

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
        """ Return the directory name of the current path. Mimics the behavior
            of `os.path.dirname`
        """
        return Path(os.path.dirname(self._pathstr))

    def abspath(self) -> "Path":
        """ Make the current path absolute """
        return Path(self._impl.abspath()._pathstr)

    def walk(self, **kwargs) -> Generator["Path", None, None]:
        """ Get a list of files below the current path

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
    """ Determine output location given a path

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
    elif abspath.startswith("bf"):
        return "bf"
    return "local"


def is_file(abspath: str) -> bool:
    """ Determines if the path is a file

    Parameters
    ----------
    abspath: str
        Path to inspect

    Returns
    -------
    bool: True if inspected path appears to be a file, otherwise False
    """
    # split into path + extension. assume no extension means a directory
    path_segments = os.path.splitext(abspath)
    if path_segments[-1] == "":
        return False
    return True


@no_type_check
def copy(src: Path, dest: Path, **kwargs):
    if src._location == "local" and dest._location == "s3":
        return copy_local_s3(src._impl, dest._impl, **kwargs)
    elif src._location == "s3" and dest._location == "s3":
        return copy_s3_s3(src._impl, dest._impl, **kwargs)
    elif src._location == "s3" and dest._location == "local":
        return copy_s3_local(src._impl, dest._impl, **kwargs)
    else:
        raise UnsupportedCopyOperation(
            "Only local -> s3, s3 -> s3, and s3 -> local are currently supported"
        )
    pass


def copy_local_s3(src: LocalPath, dest: S3Path, **kwargs):
    s3 = boto3.client("s3")
    bucket = dest.bucket
    key = dest.key
    s3.upload_file(str(src), bucket, key, ExtraArgs=kwargs)


def copy_s3_s3(src: S3Path, dest: S3Path, **kwargs):
    s3fs = S3FileSystem(anon=False)
    s3fs.copy(str(src), str(dest), **kwargs)


def copy_s3_local(src: S3Path, dest: LocalPath, **kwargs):
    s3 = boto3.client("s3")

    bucket = src.bucket
    prefix = src.key

    # copy will be recursive automatically if the src is a directory
    if src.is_dir():
        continuation_token = None
        while True:
            if continuation_token is not None:
                batch = s3.list_objects_v2(
                    Bucket=bucket, Prefix=prefix, ContinuationToken=continuation_token
                )
            else:
                batch = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

            for key in batch["Contents"]:
                key_parts = key["Key"].split("/")

                # create local directories
                destination = Path(str(dest.join(*key_parts)))
                destination.dirname().mkdir(parents=True, exist_ok=True)
                s3.download_file(
                    Bucket=bucket,
                    Key=key["Key"],
                    Filename=str(destination),
                    ExtraArgs=kwargs,
                )

            if "NextContinuationToken" in batch:
                continuation_token = batch["NextContinuationToken"]
            else:
                break

    elif src.is_file():
        if dest.is_dir():
            s3.download_file(
                Bucket=bucket,
                Key=prefix,
                Filename=str(dest / src.parts[-1]),
                ExtraArgs=kwargs,
            )
        else:
            s3.download_file(
                Bucket=bucket, Key=prefix, Filename=str(dest), ExtraArgs=kwargs,
            )
    else:
        raise UnsupportedCopyOperation("src was not a directory or a file")


def _get_collection_by_name(base, name):
    for item in base.items:
        if item.type == "Collection" and item.name == name:
            return item


def _get_package_by_name(base, name):
    for item in base.items:
        if item.type != "Collection" and item.name == name:
            return item
