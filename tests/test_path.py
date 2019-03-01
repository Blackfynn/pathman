import os
import pytest
import boto3
import functools
from moto import mock_s3
from pkg_resources import resource_filename


from pathman.path import is_file, determine_output_location, \
    LocalPath, S3Path, Path, copy_local_s3, copy


output = functools.partial(resource_filename, 'tests.output')
data = functools.partial(resource_filename, 'tests.resources')

real_bucket = "s3://test-bucket"
real_file = "s3://test-bucket/test-key/test_file.txt"


def local_file():
    return os.path.abspath(__file__)


def local_dir():
    real_file = local_file()
    return os.path.dirname(real_file)


class TestPath(object):
    @classmethod
    def setup_class(cls):
        cls.mock = mock_s3()
        cls.mock.start()
        cls.s3 = boto3.client("s3")
        cls.s3.create_bucket(Bucket="test-bucket")
        cls.s3.put_object(Body=b"Hello World",
                          Bucket="test-bucket",
                          Key="test-key/test_file.txt")

    @classmethod
    def teardown_class(cls):
        cls.mock.stop()

    @pytest.mark.parametrize("path", [
        "/some/local/dir/",
        "/some/local/file.txt"
    ])
    def test_initialize_local(self, path):
        assert isinstance(Path(path)._impl, LocalPath)

    @pytest.mark.parametrize("path, expectation", [
        ("/some/local/dir/", ""),
        ("/some/local/file.txt", ".txt"),
        ("/some/local/file.csv", ".csv"),
        ("s3://test-bucket/", ""),
        ("s3://test-bucket/file.txt", ".txt"),
        ("s3://test-bucket/file.csv", ".csv")
    ])
    def test_extension(self, path, expectation):
        assert Path(path).extension == expectation

    @pytest.mark.parametrize("path, expectation", [
        ("/some/local/dir/", ""),
        ("/some/local/file.txt", "file.txt"),
        ("s3://test-bucket/", ""),
        ("s3://test-bucket/file.txt", "file.txt")
    ])
    def test_basename(self, path, expectation):
        assert Path(path).basename() == expectation

    @pytest.mark.parametrize("file_path, mode", [
        (output("test_file.txt"), "w"),
        (output("test_file"), "wb"),
        ("s3://test-bucket/new-file.txt", "w"),
        ("s3://test-bucket/new-file.txt", "wb")
    ])
    def test_open_remove(self, file_path, mode):
        p = Path(file_path)
        assert p.exists() is False
        f = p.open(mode)
        f.close()
        assert p.exists()
        p.remove()
        assert p.exists() is False

    @pytest.mark.parametrize("file_path, mode, contents", [
        (output("test_file.txt"), "w", "test"),
        ("s3://test-bucket/new-file.txt", "w", "test")
    ])
    def test_read_write_text(self, file_path, mode, contents):
        p = Path(file_path)
        p.write_text(contents)
        retrieved = p.read_text()
        assert retrieved == contents
        p.remove()

    @pytest.mark.parametrize("file_path, mode, contents", [
        (output("test_file"), "wb", b"test"),
        ("s3://test-bucket/new-file.txt", "wb", b"test")
    ])
    def test_read_write_bytes(self, file_path, mode, contents):
        p = Path(file_path)
        p.write_bytes(contents)
        retrieved = p.read_bytes()
        assert retrieved == contents
        p.remove()

    @pytest.mark.parametrize("file_path, expect_change", [
        ("~/some/test/file.txt", False),
        ("s3://some/test/file.txt", True)
    ])
    def test_expanduser(self, file_path, expect_change):
        result = (Path(file_path).expanduser() == Path(file_path))
        assert result == expect_change

    @pytest.mark.parametrize("file_path, expected_output", [
        ("/some/dir/", "/some/dir"),
        ("some/file.txt", "some"),
        ("s3://some/dir/", "s3://some/dir"),
        ("s3://some/file.txt", "s3://some")
    ])
    def test_dirname(self, file_path, expected_output):
        assert Path(file_path).dirname() == Path(expected_output)

    @pytest.mark.parametrize("file_path, expected", [
        ("./some/relative/dir/", False),
        ("../some/relative/dir", False),
        ("s3://some/s3/path/", True)
    ])
    def test_abspath(self, file_path, expected):
        result = Path(file_path).abspath() == Path(file_path)
        assert result == expected

    @pytest.mark.parametrize("base_dir, expected_length", [
        (data("folder/"), 2),
        ("s3://test-bucket", 1)
    ])
    def test_walk(self, base_dir, expected_length):
        found_files = Path(base_dir).walk()
        assert len(found_files) == expected_length

    @pytest.mark.parametrize("base_dir, expected_length", [
        (data("folder/"), 2),
        ("s3://test-bucket/", 1)
    ])
    def test_ls(self, base_dir, expected_length):
        assert len(Path(base_dir).ls()) == expected_length

    @pytest.mark.parametrize("head, tail", [
        ["/some/dir/", "some_file.txt"],
        ["s3://test-bucket", "some_file.txt"],
    ])
    def test_truediv_join(self, head, tail):
        path = Path(head)
        assert str(path / tail) == os.path.join(head, tail)

    @pytest.mark.parametrize("base, pattern, expected", [
        (data("folder/"), "*.txt", [data("folder/") + "file2.txt",
                                    data("folder/") + "file1.txt"]),
        ("s3://test-bucket/test-key", "*.txt",
         ["s3://test-bucket/test-key/test_file.txt"])
    ])
    def test_glob(self, base, pattern, expected):
        assert Path(base).glob(pattern) == [Path(p) for p in expected]

    @pytest.mark.parametrize("path, suffix", [
        ["/some/dir/some_file", ".txt"],
        ["s3://test-bucket/some_file", ".txt"]
    ])
    def test_with_suffix(self, path, suffix):
        assert Path(path).with_suffix(suffix) == Path(path + suffix)

    @pytest.mark.parametrize("path, stem", [
        ["/some/dir/some_file.txt", "some_file"],
        ["s3://test-bucket/some_file.txt", "some_file"]
    ])
    def test_stem(self, path, stem):
        assert Path(path).stem == stem

    @pytest.mark.parametrize("path, parts", [
        ["/some/dir/file.txt", ["/", "some", "dir", "file.txt"]],
        ["c:/some/dir/file.txt", ["c:", "some", "dir", "file.txt"]],
        ["s3://test-bucket/file.txt", ["s3:", "test-bucket", "file.txt"]]
    ])
    def test_parts(self, path, parts):
        assert Path(path).parts == parts


class TestLocalPath(object):

    def test_initialize(self):
        path = LocalPath("some/test/path")
        assert str(path) == "some/test/path"

    @pytest.mark.parametrize("path, expectation", [
        (local_file(), True),
        (local_dir(), True),
        ("/some/fake/file.txt", False),
        ("/some/fake/dir", False),
        ("/some/fake/dir/", False),
        ("some/fake/dir", False)
    ])
    def test_exists(self, path, expectation):
        assert LocalPath(path).exists() == expectation

    @pytest.mark.parametrize("path,expectation", [
        (local_file(), False),
        (local_dir(), True),
        ("some/local/nonexistent/dir/", False),
        ("some/local/nonexistent/dir", False),
    ])
    def test_is_dir(self, path, expectation):
        assert LocalPath(path).is_dir() == expectation

    @pytest.mark.parametrize("path,expectation", [
        (local_file(), True),
        (local_dir(), False),
        ("some/local/nonexistent/file/file.txt", False),
    ])
    def test_is_file(self, path, expectation):
        assert LocalPath(path).is_file() == expectation

    def test_mkdir(self):
        to_create = os.path.join(local_dir(), "testdir")
        path = LocalPath(to_create)
        path.mkdir()
        assert os.path.exists(to_create)
        os.rmdir(to_create)

    def test_rmdir(self):
        to_create = os.path.join(local_dir(), "testdir")
        os.mkdir(to_create)
        path = LocalPath(to_create)
        path.rmdir()
        assert os.path.exists(to_create) is False

    @pytest.mark.parametrize("segments", [
        ["/some/dir/", "some_file.txt"],
        ["/some/dir", "some_file.txt"],
        ["some/dir", "some_file.txt"],
        ["some/dir/", "some_file.txt"],
    ])
    def test_join(self, segments):
        path = LocalPath("")
        assert str(path.join(*segments)) == os.path.join("", *segments)


class TestS3Path(object):
    @classmethod
    def setup_class(cls):
        cls.mock = mock_s3()
        cls.mock.start()
        cls.s3 = boto3.client("s3")
        cls.s3.create_bucket(Bucket="test-bucket")
        cls.s3.put_object(Body=b"Hello World",
                          Bucket="test-bucket",
                          Key="test-key/test_file.txt")

    @classmethod
    def teardown_class(cls):
        cls.mock.stop()

    def test_initialize(self):
        path = S3Path("s3://some/test/path")
        assert str(path) == "s3://some/test/path"

    @pytest.mark.parametrize("path, expectation", [
        (real_bucket, True),
        (real_file, True),
        ("s3://fake-test-bucket/test_file.txt", False),
        ("s3://test-bucket/fake_file.txt", False),
        ("s3://test-bucket/", True),
        ("s3://test-bucket/test-key/", True)
    ])
    def test_exists(self, path, expectation):
        assert S3Path(path).exists() == expectation

    @pytest.mark.parametrize("path,expectation", [
        (real_bucket, True),
        (real_file, False),
        ("s3://fake-test-bucket/test_file.txt", False),
        ("s3://test-bucket/fake_file.txt", False),
        ("s3://test-bucket/", True),
        ("s3://test-bucket/test-key/", True)
    ])
    def test_is_dir(self, path, expectation):
        assert S3Path(path).is_dir() == expectation

    @pytest.mark.parametrize("path,expectation", [
        (real_bucket, False),
        (real_file, True),
        ("s3://fake-test-bucket/test_file.txt", False),
        ("s3://test-bucket/fake_file.txt", False),
        ("s3://test-bucket/", False),
        ("s3://test-bucket/test-key/", False)
    ])
    def test_is_file(self, path, expectation):
        assert S3Path(path).is_file() == expectation

    def test_mkdir(self):
        to_create = "s3://new-bucket"
        path = S3Path(to_create)
        path.mkdir()
        all_bucket_resp = self.s3.list_buckets()
        bucket_names = [b['Name'] for b in all_bucket_resp['Buckets']]
        assert "new-bucket" in bucket_names

        self.s3.delete_bucket(Bucket="new-bucket")

    def test_rmdir(self):
        self.s3.create_bucket(Bucket="new-bucket")
        path = S3Path("s3://new-bucket")
        path.rmdir()
        all_bucket_resp = self.s3.list_buckets()
        bucket_names = [b['Name'] for b in all_bucket_resp['Buckets']]
        assert "new-bucket" not in bucket_names

    def test_rmdir_recursive(self):
        self.s3.create_bucket(Bucket="new-bucket")
        self.s3.put_object(Body=b"Hello World",
                           Bucket="new-bucket",
                           Key="test-key/test_file.txt")
        path = S3Path("s3://new-bucket/test-key")
        assert path.exists()
        path.rmdir(recursive=True)
        assert path.exists() is False
        assert path.join("test-key").exists() is False

    @pytest.mark.parametrize("segments", [
        ["s3://some/dir/", "some_file.txt"],
        ["s3://some/dir", "some_file.txt"],
        ["s3://some-bucket", "some-key"],
        ["s3://some-bucket/", "some-key"],
    ])
    def test_join(self, segments):
        path = S3Path("")
        assert str(path.join(*segments)) == os.path.join("", *segments)

    @pytest.mark.parametrize("path, expectation", [
        ("s3://some/dir/", "dir/"),
        ("s3://some/dir", "dir"),
        ("s3://some/dir/file.txt", "dir/file.txt"),
        ("s3://some/file.txt", "file.txt")
    ])
    def test_key(self, path, expectation):
        assert S3Path(path).key == expectation

    @pytest.mark.parametrize("path, expectation", [
        ("s3://some/dir/", "some"),
        ("s3://some/dir", "some"),
        ("s3://some/dir/file.txt", "some"),
        ("s3://some/file.txt", "some"),
        ("s3://some-bucket/file.txt", "some-bucket")
    ])
    def test_bucket(self, path, expectation):
        assert S3Path(path).bucket == expectation


@pytest.mark.parametrize("path,expectation", [
   ("/some/local/file.txt", True),
   ("/some/local/dir/", False),
   ("some/local/dir/", False),
   ("some/local/dir", False),
   ("s3://some/remote/file.txt", True),
   ("s3://some/remote/dir/", False),
   ("s3://some/remote/dir", False)

])
def test_is_file(path, expectation):
    assert is_file(path) == expectation


@pytest.mark.parametrize("path,expectation", [
   ("/some/local/file.txt", "local"),
   ("/some/local/dir/", "local"),
   ("some/local/dir/", "local"),
   ("some/local/dir", "local"),
   ("s3://some/remote/file.txt", "s3"),
   ("s3://some/remote/dir/", "s3"),
   ("s3://some/remote/dir", "s3")
])
def test_determine_output_location(path, expectation):
    assert determine_output_location(path) == expectation


@mock_s3
def test_copy_local_s3():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="test-bucket")
    remote_file = S3Path("test-bucket/test.py")
    copy_local_s3(LocalPath(local_file()), remote_file)
    assert remote_file.exists()


@mock_s3
def test_copy():
    # Currently only testing local -> s3
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="test-bucket")
    remote_file = Path("s3://test-bucket/test.py")
    local_file_path = Path(local_file())
    copy(local_file_path, remote_file)
    assert remote_file.exists()

