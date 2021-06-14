import logging
import os
import shutil

import pytest
import requests

import main
from library import backend, config

logger = logging.getLogger(__name__)
logger = backend.set_logger(logger, "tests.log")

# print("  SETUP otherarg", param)
# yield param
# print("  TEARDOWN otherarg", param)


@pytest.fixture(scope="module")
def create_config():
    conf_result = config.Config("test_main.ini")
    # Modify config with known failures to test
    conf_result.parser["Main Test/A"] = {
        "days": "2000",
        "ratings": "s",
        "min_score": "1000",
        "tags": "cat",
    }
    conf_result.parser["Main Test/B"] = {
        "days": "2000",
        "ratings": "s, q",
        "min_score": "1000",
        "tags": "cat",
    }
    conf_result.parser["URI"]["uri"] = os.environ["URI"]  # Required test field
    conf_result._parse_config()  # re-run configuration
    with open(conf_result.filepath, "w") as cfg:
        conf_result.parser.write(cfg)
    yield conf_result
    os.remove(conf_result.filepath)


@pytest.fixture(params=[False, True], ids=["Fake API", "Real API"])
def create_config_api(request, create_config):
    correct_keys = request.param
    create_config.parser["URI"]["api"] = (
        os.environ["API"] if "API" in os.environ and correct_keys else "test_api_key"
    )
    create_config.parser["URI"]["user"] = (
        os.environ["USER"] if "USER" in os.environ and correct_keys else "test_user"
    )
    create_config.api, create_config.user = create_config._get_api_key()
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
    if create_config_api.user == "test_user":
        with pytest.raises(requests.RequestException):
            main.Downloader("test_main.ini")
    else:
        result = main.Downloader("test_main.ini")
        path = os.path.normpath(result.path + "/downloads/Main Test/")
        assert os.path.isdir(path)
        shutil.rmtree(path)  # removes test directory
