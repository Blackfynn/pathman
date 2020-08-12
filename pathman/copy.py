import importlib
from concurrent import futures
from typing import no_type_check, Optional

from pathman._impl import S3Path, LocalPath
from pathman.exc import UnsupportedCopyOperation
from pathman.path import Path

try:
    s3fs = importlib.import_module("s3fs")
except ImportError:
    raise ImportError("s3fs is required to use copy")

from s3fs import S3FileSystem  # type: ignore

try:
    importlib.import_module("boto3")  # type: ignore
except ImportError:
    raise ImportError("boto3 is required to use copy")

import boto3  # type: ignore


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


def copy_s3_local(
    src: S3Path, dest: LocalPath, parallelism: Optional[int] = None, **kwargs
):
    s3 = boto3.client("s3")

    bucket = src.bucket
    prefix = src.key
    prefix_parts = prefix.split("/")

    def _download_key(key: str):
        key_parts = key.split("/")[len(prefix_parts) :]

        # create local directories
        destination = Path(str(dest.join(*key_parts)))
        destination.dirname().mkdir(parents=True, exist_ok=True)
        s3.download_file(
            Bucket=bucket, Key=key, Filename=str(destination), ExtraArgs=kwargs
        )

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

            with futures.ThreadPoolExecutor(max_workers=parallelism) as executor:
                futures.wait(
                    [
                        executor.submit(_download_key, key["Key"])
                        for key in batch["Contents"]
                    ],
                    return_when=futures.FIRST_EXCEPTION,
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
                Bucket=bucket, Key=prefix, Filename=str(dest), ExtraArgs=kwargs
            )
    else:
        raise UnsupportedCopyOperation(
            "src was not a directory or a file: {}".format(src)
        )
