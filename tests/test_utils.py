import pytest

from pathman.utils import is_file


@pytest.mark.parametrize(
    "path,expectation",
    [
        ("/some/local/file.txt", True),
        ("/some/local/dir/", False),
        ("some/local/dir/", False),
        ("some/local/dir", False),
        ("s3://some/remote/file.txt", True),
        ("s3://some/remote/dir/", False),
        ("s3://some/remote/dir", False),
    ],
)
def test_is_file(path, expectation):
    assert is_file(path) == expectation
