from abc import ABC, abstractmethod, abstractproperty
from typing import Dict, List
import os


class MetaPath(type, ABC):
    """
    A metaclass for `AbstractPath`. Whenever a class inherits from
    `AbtractPath`, if it has a `prefix` property, it will be registered
    in the `AbstractPath.paths` dictionary so that the `Path` constructor
    can automatically use the correct implementation based on the path string.
    """

    def __new__(cls, name, bases, namespace, **kwargs):
        result = super().__new__(cls, name, bases, namespace)
        if 'prefix' in namespace:
            AbstractPath.paths[namespace['prefix']] = result

        return result


class AbstractPath(metaclass=MetaPath):
    """ Defines the interface for all Path-like objects """

    # This dict is automatically populated at runtime with all classes
    # which inherit from AbstractPath and implement a prefix property.
    paths: Dict[str, 'AbstractPath'] = {}

    @abstractmethod
    def __init__(self, path: str, *args, **kwargs):
        self._pathstr = path

    @abstractproperty
    def extension(self):
        """ Get the extension if the path is a file """
        pass

    @abstractmethod
    def exists(self):
        """ Checks if the path exists """
        pass

    @abstractmethod
    def touch(self):
        """ Create a file at the current path """
        pass

    @abstractmethod
    def is_dir(self) -> bool:
        """ Checks if the path is a directory """
        pass

    @abstractmethod
    def is_file(self) -> bool:
        """ Checks if the path is a file """
        pass

    @abstractmethod
    def mkdir(self):
        """ Make a new directory """
        pass

    @abstractmethod
    def rmdir(self, recursive: bool = False):
        """ Remove a directory

        Parameters
        ----------
        recursive : bool, optional
            If True, remove directory and all contents recursively.
            If False, the directory must be empty

        """
        pass

    @abstractmethod
    def join(self, *pathsegments: str) -> 'AbstractPath':
        """ Combine the current path with the given segments """
        pass

    @abstractmethod
    def open(self, mode="r", **kwargs):
        """ Open a file similar to built-in open() function

        Parameters
        ----------
        mode: str, optional
            Mode to use when opening the file

        Returns
        -------
        file object: object

        """
        pass

    @abstractmethod
    def write_bytes(self, contents: bytes, **kwargs):
        """ Open file, write bytes, and close the file

        Parameters
        ----------
        contents: bytes
            Content to write to the file

        Returns
        -------
        number of bytes written: int

        """
        pass

    @abstractmethod
    def write_text(self, contents: str, **kwargs):
        """ Open file, write text, and close file

        Parameters
        ----------
        contents: str
            Content to write to the file

        Returns
        -------
        number of characters written: int

        """
        pass

    @abstractmethod
    def read_bytes(self, **kwargs) -> bytes:
        """ Open file, read bytes, and close file """
        pass

    @abstractmethod
    def read_text(self, **kwargs) -> str:
        """ Open file, read text, and close file """
        pass

    @abstractmethod
    def remove(self):
        """
            Remove this file. If the path points to a directory, use rmdir
            instead
        """
        pass

    @abstractmethod
    def expanduser(self) -> 'AbstractPath':
        """ Return a new path with ``~`` expanded """
        pass

    @abstractmethod
    def abspath(self) -> 'AbstractPath':
        """ Make the current path absolute """
        pass

    @abstractmethod
    def walk(self):
        """ Get a list of files below the current path

        Note
        ----
        This does not mirror the behavior of `os.walk`. A list of absolute
        paths are returned
        """
        pass

    @abstractmethod
    def ls(self):
        """ Returns a list of the files and folders in this directory """
        pass

    @abstractmethod
    def __truediv__(self, key):
        pass

    @abstractmethod
    def glob(self, pattern: str):
        """ Matches the folders and file in this directory with the provided
        pattern

        Parameters
        ----------
        pattern:
            The pattern to be matched

        Returns
        -------
        A list of path objects: ``List[Path]``

        """
        pass

    @abstractmethod
    def with_suffix(self, suffix) -> 'AbstractPath':
        """ Returns a Path with `suffix` added to the end of the this path """
        pass

    @abstractproperty
    def stem(self) -> str:
        """ Returns the name of this file or folder with out an extension """
        pass

    @abstractproperty
    def parts(self) -> List[str]:
        """ Returns the tokens that make up this object's path """
        pass

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

    def dirname(self) -> str:
        """ Return the directory name of the current path. Mimics the behavior
            of `os.path.dirname`
        """
        return os.path.dirname(self._pathstr)


class RemotePath(object):
    """ A mixin that represents any non-local path

    Notes
    -----
        This can be used to add additional methods to remote files
        that are specific to managing remote resources. This will
        also allow us to unify the API for managing remote resources
        across cloud providers should that be necessary in the future.
    """
