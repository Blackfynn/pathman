import pytest
import boto3
import os
from moto import mock_s3
from pathman import S3Path
from .test_path import real_file

real_bucket = "s3://test-bucket"


class TestS3Path(object):
    @classmethod
    def setup_class(cls):
        cls.mock = mock_s3()
        cls.mock.start()
        cls.s3 = boto3.client("s3")
        cls.s3.create_bucket(Bucket="test-bucket")
        cls.s3.put_object(
            Body=b"Hello World", Bucket="test-bucket", Key="test-key/test_file.txt"
        )

    @classmethod
    def teardown_class(cls):
        cls.mock.stop()

    def test_initialize(self):
        path = S3Path("s3://some/test/path")
        assert str(path) == "s3://some/test/path"

    @pytest.mark.parametrize(
        "path, expectation",
        [
            (real_bucket, True),
            (real_file, True),
            ("s3://fake-test-bucket/test_file.txt", False),
            ("s3://test-bucket/fake_file.txt", False),
            ("s3://test-bucket/", True),
            ("s3://test-bucket/test-key/", True),
        ],
    )
    def test_exists(self, path, expectation):
        assert S3Path(path).exists() == expectation

    @pytest.mark.parametrize(
        "path,expectation",
        [
            (real_bucket, True),
            (real_file, False),
            ("s3://fake-test-bucket/test_file.txt", False),
            ("s3://test-bucket/fake_file.txt", False),
            ("s3://test-bucket/", True),
            ("s3://test-bucket/test-key/", True),
        ],
    )
    def test_is_dir(self, path, expectation):
        assert S3Path(path).is_dir() == expectation

    @pytest.mark.parametrize(
        "path,expectation",
        [
            (real_bucket, False),
            (real_file, True),
            ("s3://fake-test-bucket/test_file.txt", False),
            ("s3://test-bucket/fake_file.txt", False),
            ("s3://test-bucket/", False),
            ("s3://test-bucket/test-key/", False),
        ],
    )
    def test_is_file(self, path, expectation):
        assert S3Path(path).is_file() == expectation

    def test_mkdir(self):
        to_create = "s3://new-bucket"
        path = S3Path(to_create)
        path.mkdir()
        all_bucket_resp = self.s3.list_buckets()
        bucket_names = [b["Name"] for b in all_bucket_resp["Buckets"]]
        assert "new-bucket" in bucket_names

        self.s3.delete_bucket(Bucket="new-bucket")

    def test_rmdir(self):
        self.s3.create_bucket(Bucket="new-bucket")
        path = S3Path("s3://new-bucket")
        path.rmdir()
        all_bucket_resp = self.s3.list_buckets()
        bucket_names = [b["Name"] for b in all_bucket_resp["Buckets"]]
        assert "new-bucket" not in bucket_names

    def test_rmdir_recursive(self):
        self.s3.create_bucket(Bucket="new-bucket")
        self.s3.put_object(
            Body=b"Hello World", Bucket="new-bucket", Key="test-key/test_file.txt"
        )
        path = S3Path("s3://new-bucket/test-key")
        assert path.exists()
        path.rmdir(recursive=True)
        assert path.exists() is False
        assert path.join("test-key").exists() is False

    @pytest.mark.parametrize(
        "segments",
        [
            ["s3://some/dir/", "some_file.txt"],
            ["s3://some/dir", "some_file.txt"],
            ["s3://some-bucket", "some-key"],
            ["s3://some-bucket/", "some-key"],
        ],
    )
    def test_join(self, segments):
        path = S3Path("")
        assert str(path.join(*segments)) == os.path.join("", *segments)

    @pytest.mark.parametrize(
        "path, expectation",
        [
            ("s3://some/dir/", "dir/"),
            ("s3://some/dir", "dir"),
            ("s3://some/dir/file.txt", "dir/file.txt"),
            ("s3://some/file.txt", "file.txt"),
        ],
    )
    def test_key(self, path, expectation):
        assert S3Path(path).key == expectation

    @pytest.mark.parametrize(
        "path, expectation",
        [
            ("s3://some/dir/", "some"),
            ("s3://some/dir", "some"),
            ("s3://some/dir/file.txt", "some"),
            ("s3://some/file.txt", "some"),
            ("s3://some-bucket/file.txt", "some-bucket"),
        ],
    )
    def test_bucket(self, path, expectation):
        assert S3Path(path).bucket == expectation
