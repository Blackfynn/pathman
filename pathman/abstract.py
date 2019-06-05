from abc import ABC, abstractmethod, abstractproperty
from typing import Dict


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
    def mkdir(self):
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
    def walk(self):
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


class RemotePath(object):
    """ A mixin that represents any non-local path

    Notes
    -----
        This can be used to add additional methods to remote files
        that are specific to managing remote resources. This will
        also allow us to unify the API for managing remote resources
        across cloud providers should that be necessary in the future.
    """
