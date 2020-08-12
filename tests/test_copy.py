import os
import random
import string
import shutil

import boto3  # type: ignore
from moto import mock_s3  # type: ignore

from pathman.path import Path
from pathman._impl import S3Path, LocalPath

from pathman.copy import copy_local_s3, copy_s3_local, copy


def random_bucket() -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(10))


@mock_s3
def test_copy_local_s3(local_file):
    s3 = boto3.client("s3")
    bucket = random_bucket()
    s3.create_bucket(Bucket=bucket)
    remote_file = S3Path("{}/test.py".format(bucket))
    copy_local_s3(LocalPath(local_file), remote_file)
    assert remote_file.exists()


@mock_s3
def test_copy(local_file):
    s3 = boto3.client("s3")
    bucket = random_bucket()
    s3.create_bucket(Bucket=bucket)
    remote_file = Path("s3://{}/test.py".format(bucket))
    local_file_path = Path(local_file)
    copy(local_file_path, remote_file)
    assert remote_file.exists()


@mock_s3
def test_copy_s3_local_file(local_file, local_dir):
    s3 = boto3.client("s3")
    bucket = random_bucket()

    s3.create_bucket(Bucket=bucket)
    s3.upload_file(local_file, bucket, "test.py")

    local_test_file = Path(os.path.join(local_dir, "test.py"))
    copy_s3_local(S3Path("s3://{}/test.py".format(bucket)), local_test_file)

    assert local_test_file.exists()
    local_test_file.remove()


@mock_s3
def test_copy_s3_local_file_supports_dest_dir(local_file, local_dir):
    s3 = boto3.client("s3")
    bucket = random_bucket()

    s3.create_bucket(Bucket=bucket)
    s3.upload_file(local_file, bucket, "test.py")

    local_test_file = Path(os.path.join(local_dir, "test.py"))

    # This should accept a directory argument
    copy_s3_local(S3Path("s3://{}/test.py".format(bucket)), Path(local_dir))

    assert local_test_file.exists()
    local_test_file.remove()


@mock_s3
def test_copy_s3_local_recursive(local_file, local_dir):
    s3 = boto3.client("s3")
    bucket = random_bucket()

    s3.create_bucket(Bucket=bucket)

    s3.upload_file(local_file, bucket, "basedir/test.py")
    s3.upload_file(local_file, bucket, "basedir/subdir/test.py")
    s3.upload_file(local_file, bucket, "basedir/subdir/test2.py")
    s3.upload_file(local_file, bucket, "basedir/subdir/subdir/test.py")

    root_path = Path(os.path.join(local_dir, "basedir"))
    copy_s3_local(S3Path("s3://{}/basedir".format(bucket)), root_path)

    try:
        assert root_path.exists()
        assert (root_path / "test.py").exists()
        assert (root_path / "subdir").exists()
        assert (root_path / "subdir" / "test.py").exists()
        assert (root_path / "subdir" / "test2.py").exists()
        assert (root_path / "subdir" / "subdir").exists()
        assert (root_path / "subdir" / "subdir" / "test.py").exists()

    finally:
        shutil.rmtree(root_path, ignore_errors=True)
