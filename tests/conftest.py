import pytest

from library import config


@pytest.fixture()
def collect_config():
    return config.Config("test.ini")
