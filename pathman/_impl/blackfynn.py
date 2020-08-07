import os
import re
import logging
import importlib
from tempfile import TemporaryDirectory
from typing import Generator, List

import requests

from pathman.base import AbstractPath, RemotePath


class BlackfynnPath(AbstractPath, RemotePath):
    """ Representation of a path on the Blackfynn platform """

    def __init__(self, path: str, dataset=None, profile="default", **kwargs):
        try:
            importlib.import_module("blackfynn")
        except ImportError:
            raise ImportError("blackfynn client is required for BlackfynnPath")

        from blackfynn import Blackfynn  # type: ignore
        from blackfynn.models import BaseDataNode  # type: ignore

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


def _get_collection_by_name(base, name):
    for item in base.items:
        if item.type == "Collection" and item.name == name:
            return item


def _get_package_by_name(base, name):
    for item in base.items:
        if item.type != "Collection" and item.name == name:
            return item
