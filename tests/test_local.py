import pytest
import os
from .test_path import local_file, local_dir
from pathman import LocalPath, Path


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
