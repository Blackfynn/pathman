import os
import pytest


@pytest.fixture(scope="function")
def local_file():
    return os.path.abspath(__file__)


@pytest.fixture(scope="function")
def local_dir(local_file):
    return os.path.dirname(local_file)
