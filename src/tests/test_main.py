import logging
import os
import shutil

import pytest
import requests

from src import main
from src.library import backend, config

logger = logging.getLogger(__name__)
logger = backend.set_logger(logger, "tests.log")


# print("  SETUP otherarg", param)
# yield param
# print("  TEARDOWN otherarg", param)


@pytest.fixture(scope="module")
def create_config():
    conf_result = config.Config("test_main.ini")
    # Modify config with known failures to test
    # correct assumptions of a section
    conf_result.parser["Main Test/Correct_Section"] = {
        "days": "2000",
        "ratings": "s",
        "min_score": "1000",
        "tags": "cat",
    }
    # will trigger blacklist
    conf_result.parser["Main Test/Blacklist_Trigger"] = {
        "days": "20",
        "ratings": "s, q",
        "min_score": "20",
        "tags": "canine",
        "ignore_tags": "",
        "allowed_types": "",
    }
    # will ignore blacklist AND change allowed types to only png
    conf_result.parser["Main Test/Ignore_Blacklist_PNG_Only"] = {
        "days": "20",
        "ratings": "s, q",
        "min_score": "100",
        "tags": "canine",
        "ignore_tags": "canine",
        "allowed_types": "png",
    }
    # will trigger min_faves
    conf_result.parser["Main Test/Min_Faves_Trigger"] = {
        "days": "20",
        "ratings": "s",
        "min_score": "100",
        "min_faves": "200",
        "tags": "canine",
        "ignore_tags": "canine",
        "allowed_types": "png",
    }
    # will trigger rating miss
    conf_result.parser["Main Test/Rating_Trigger"] = {
        "days": "5",
        "ratings": "q, e",
        "min_score": "200",
        "min_faves": "200",
        "tags": "canine",
        "ignore_tags": "canine",
        "allowed_types": "png",
    }

    conf_result.parser["URI"]["uri"] = os.environ["URI"]  # Required test field
    conf_result._parse_config()  # re-run configuration
    with open(conf_result.filepath, "w") as cfg:
        conf_result.parser.write(cfg)
    yield conf_result
    os.remove(conf_result.filepath)


@pytest.fixture(
    params=[False, True],
    ids=["Fake API [Force Program Crash]", "Real API [Download with API key]"],
)
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


def test_bad_download():
    """Runs through "already exists" code paths
    Removes files afterward for next test
    """
    conf_result = config.Config("test.ini")
    conf_result.parser["URI"]["uri"] = os.environ["URI"]  # Required test field
    conf_result._parse_config()
    with open(conf_result.filepath, "w") as cfg:
        conf_result.parser.write(cfg)
    result = main.Downloader("test.ini")
    result.download_file(
        result.session,
        f'{os.environ["URI"]}/bad_download.png',
        "Bad Data",
        "bad_download",
    )
    os.remove(conf_result.filepath)


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
