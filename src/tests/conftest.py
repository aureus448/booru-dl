import pytest

from src.library import backend, config


@pytest.fixture()
def collect_config():
    return config.Config("test.ini")


@pytest.fixture
def get_session(collect_config):
    """Uses config to collect a session instance"""
    return backend.get_session(collect_config.useragent)
