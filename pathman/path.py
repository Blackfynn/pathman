""" Module for abstracting over local/remote file paths """
import os
import boto3  # type: ignore
from typing import no_type_check
from pathman.exc import UnsupportedPathTypeException, UnsupportedCopyOperation
from s3fs import S3FileSystem  # type: ignore

from pathman.s3 import S3Path
from pathman.local import LocalPath
from pathman.abstract import AbstractPath, MetaPath
from pathman.utils import is_file


class MetaPathLike(MetaPath, os.PathLike):
    """
    Allows `Path` to inherit from `AbstractPath` and `os.PathLike` without
    interference between their metaclasses.
    """
    pass


class Path(metaclass=MetaPathLike):
    """ Represents a generic path object """

    def __new__(cls, path: str, *args, **kwargs) -> None:
        """ Constructor for a new Path

        Parameters
        ----------
        path: str or path-like object
           A path string
        """
        path = str(path)
        location: str = determine_output_location(path)
        if location not in AbstractPath.paths:
            raise UnsupportedPathTypeException(
                "inferred location is not supported for {}".format(path))
        result = AbstractPath.paths[location](path, *args, **kwargs)

        result._location = location
        result._pathstr = path
        result._isfile = is_file(path)

        return result


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
    Compares the beginning of `abspath` to all of the regisered Path classes.
    If no match is found, default to "local"
    """
    for key in AbstractPath.paths:
        if abspath.startswith(key):
            return key
    return "local"


@no_type_check
def copy(src: AbstractPath, dest: AbstractPath, **kwargs):
    if src._location == "local" and dest._location == "s3":
        return copy_local_s3(src, dest, **kwargs)
    elif src._location == "s3" and dest._location == "s3":
        return copy_s3_s3(src, dest, **kwargs)
    else:
        raise UnsupportedCopyOperation(
            "Only local -> s3 and s3 -> s3 are currently supported")
    pass


def copy_local_s3(src: LocalPath, dest: S3Path, **kwargs):
    s3 = boto3.client("s3")
    bucket = dest.bucket
    key = dest.key
    s3.upload_file(str(src), bucket, key, ExtraArgs=kwargs)


def copy_s3_s3(src: S3Path, dest: S3Path, **kwargs):
    s3fs = S3FileSystem(anon=False)
    s3fs.copy(str(src), str(dest), **kwargs)
