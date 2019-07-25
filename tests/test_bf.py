import pytest
import mock
import os
import urllib
from blackfynn import Blackfynn
from tempfile import TemporaryDirectory
from pathman.bf import BlackfynnPath


class MockBlackfynn(Blackfynn):
    def __init__(self, profile=None, *args, **kwargs):
        token = os.environ.get("BLACKFYNN_API_TOKEN", None)
        secret = os.environ.get("BLACKFYNN_API_SECRET", None)
        if token and secret:
            super().__init__(api_token=token, api_secret=secret)
        else:
            super().__init__(profile)


@pytest.mark.integration
@mock.patch("pathman.bf.Blackfynn", new=MockBlackfynn)
class TestBlackfynnPath(object):
    @classmethod
    def setup_class(cls):
        bf = MockBlackfynn()
        try:
            old_ds = bf.get_dataset("test-pathman")
            bf._api.datasets.delete(old_ds)
        except Exception:
            pass
        cls.ds = bf.create_dataset("test-pathman")
        cls.ds.create_collection("folder")
        with TemporaryDirectory() as tmp:
            f_path = "{}/file.txt".format(tmp)
            with open(f_path, "w") as f:
                f.write("Hello, World!")
            cls.ds.upload(f_path)
            t_path = "{}/table.csv".format(tmp)
            with open(t_path, "w") as f:
                f.write("col1,col2\n1,A\n2,B\n3,C")
            cls.ds.upload(t_path)

    @classmethod
    def teardown_class(cls):
        bf = Blackfynn()
        bf._api.datasets.delete(cls.ds)

    def test_initialize(self):
        path = BlackfynnPath("bf://folder/subfolder/file.txt", self.ds.name)
        assert str(path) == "bf://{ds}/folder/subfolder/file".format(ds=self.ds.name)
        assert path.dataset == self.ds.name
        assert path._profile == "default"
        assert path._extension == ".txt"

    @pytest.mark.parametrize(
        "path,expectation",
        [
            ("bf://test-pathman/", True),
            ("bf://test-pathman/folder/", True),
            ("bf://test-pathman/folder/subfolder/", False),
            ("bf://test-pathman/file.txt", True),
            ("bf://test-pathman/table.csv", True),
        ],
    )
    def test_exists(self, path, expectation):
        assert BlackfynnPath(path).exists() == expectation

    @pytest.mark.parametrize(
        "path,expectation",
        [
            ("bf://test-pathman/", True),
            ("bf://test-pathman/folder/", True),
            ("bf://test-pathman/folder/subfolder/", False),
            ("bf://test-pathman/file.txt", False),
            ("bf://test-pathman/table.csv", False),
        ],
    )
    def test_is_dir(self, path, expectation):
        assert BlackfynnPath(path).is_dir() == expectation

    @pytest.mark.parametrize(
        "path,expectation",
        [
            ("bf://test-pathman/", False),
            ("bf://test-pathman/folder/", False),
            ("bf://test-pathman/folder/subfolder/", False),
            ("bf://test-pathman/file.txt", True),
            ("bf://test-pathman/table.csv", True),
        ],
    )
    def test_is_file(self, path, expectation):
        assert BlackfynnPath(path).is_file() == expectation

    def test_ls(self):
        expectations = [
            "bf://test-pathman/folder",
            "bf://test-pathman/file.txt",
            "bf://test-pathman/table.csv",
        ]
        path = BlackfynnPath("bf://", self.ds.name)
        files = [str(_file) + _file.extension for _file in path.ls()]
        for file in files:
            assert str(file) in expectations

    def test_walk(self):
        path = BlackfynnPath("bf://", self.ds.name)
        files = path.walk()
        assert len(files) == 2

    @pytest.mark.parametrize(
        "pattern, expected_length", [("*.txt", 1), ("*.*", 2), ("*/*.*", 0)]
    )
    def test_glob(self, pattern, expected_length):
        path = BlackfynnPath("bf://", self.ds.name)
        files = path.glob(pattern)
        assert len(files) == expected_length

    def test_mkdir(self):
        path = BlackfynnPath("bf://folder/test_mkdir", self.ds.name)
        assert path.exists() is False
        path.mkdir()
        assert path.is_dir() is True and path.exists() is True
        path._bf_object.delete()

    def test_rmdir(self):
        self.ds.create_collection("test_remove")
        path = BlackfynnPath("bf://test_remove", self.ds.name)
        assert path.exists() is True and path.is_dir() is True
        path.rmdir()
        assert path.exists() is False

    def test_write(self):
        path = BlackfynnPath("bf://write.txt", self.ds.name)
        to_write = "Hello, World!"
        path.write_text(to_write)
        retrieved = urllib.request.urlopen(path._bf_object.sources[0].url).read()
        assert str(retrieved, "utf-8") == "Hello, World!"
        path._bf_object.delete()

    def test_read(self):
        path = BlackfynnPath("bf://file.txt", self.ds.name)
        assert path.read_text() == "Hello, World!"

    def test_touch(self):
        path = BlackfynnPath("bf://touch.txt", self.ds.name)
        assert path.exists() is False
        path.touch()
        assert path.exists() is True and path.is_file() is True

    def test_remove(self):
        path = BlackfynnPath("bf://remove.txt", self.ds.name)
        assert path.exists() is False
        path.touch()
        assert path.exists() is True
        path.remove()
        assert path.exists() is False
