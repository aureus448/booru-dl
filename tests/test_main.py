import logging
import os
import shutil

import pytest

import main
from library import config

logger = logging.getLogger(__name__)


@pytest.fixture
def create_config():
    conf_result = config.Config("test_main.ini")
    # Modify config with known failures to test
    conf_result.parser["Main Test"] = {
        "days": "2000",
        "ratings": "s",
        "min_score": "1000",
    }
    conf_result.parser["URI"]["uri"] = os.environ["URI"]
    with open(conf_result.filepath, "w") as cfg:
        conf_result.parser.write(cfg)
    return conf_result


@pytest.fixture
def create_config_api(create_config):
    create_config.parser["URI"]["api"] = "test_api_key"
    create_config.parser["URI"]["user"] = "test_user"
    with open(create_config.filepath, "w") as cfg:
        create_config.parser.write(cfg)
    return create_config


def test_download_files(create_config):

    result = main.Downloader("test_main.ini")
    path = os.path.normpath(result.path + "/downloads/Main Test/")
    assert os.path.isdir(path)


def test_download_files_already_exist(create_config):
    """Runs through "already exists" code paths
    Removes files afterward for next test
    """
    result = main.Downloader("test_main.ini")
    path = os.path.normpath(result.path + "/downloads/Main Test/")
    assert os.path.isdir(path)
    os.remove(create_config.filepath)  # removes created config file
    shutil.rmtree(path)  # removes test directory


def test_download_files_api(create_config_api):
    """Uses the api, and forces a 401 error to occur - If it doesn't crash the test is a success"""
    main.Downloader("test_main.ini")


def test_remove_test_files(create_config):
    """Re-run and make sure main goes through non-run config as well as doesn't
    produce any output vs the _already_exist run configuration"""
    result = main.Downloader("test_main.ini", run=False)
    path = os.path.normpath(result.path + "/downloads/Main Test/")
    assert not os.path.isdir(path)
    os.remove(create_config.filepath)  # removes created config file
