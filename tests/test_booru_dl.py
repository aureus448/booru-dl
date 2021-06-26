import os
import shutil

import pytest
import requests

import booru_dl

# print("  SETUP otherarg", param)
# yield param
# print("  TEARDOWN otherarg", param)


@pytest.fixture(scope="module")
def create_config():
    conf_result = booru_dl.Config("test_main.ini")
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


@pytest.fixture(scope="module")
def create_config_exist():
    conf_result = booru_dl.Config("test_main_exist.ini")
    conf_result.parser["Main Test/Correct_Section"] = {
        "days": "2000",
        "ratings": "s",
        "min_score": "1000",
        "tags": "cat",
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


@pytest.fixture(scope="module")
def download_file():
    result = booru_dl.Downloader("test_main.ini")
    yield result
    shutil.rmtree(result.path / "downloads/Main Test/")


def test_download_files(download_file, create_config):
    result = booru_dl.Downloader("test_main.ini")
    path = result.path / "downloads/Main Test/"
    assert os.path.isdir(path)


def test_bad_download(download_file):
    """Sends a bad file to downloader"""
    result = download_file.download_file(
        download_file.session,
        f'{os.environ["URI"]}/bad_download.png',
        "Bad Data",
        "bad_download",
    )
    assert result == -1


def test_download_files_already_exist(create_config_exist):
    """Runs through "already exists" code paths
    Removes files afterward for next test
    """
    result = booru_dl.Downloader("test_main_exist.ini")
    path = result.path / "downloads/Main Test/"
    assert os.path.isdir(path)


def test_download_files_api(download_file, create_config_api):
    """Uses the api, and forces a 401 error to occur - If it doesn't crash the test is a success"""
    if create_config_api.user == "test_user":
        with pytest.raises(requests.RequestException):
            booru_dl.Downloader("test_main.ini")
    else:
        result = booru_dl.Downloader("test_main.ini")
        path = result.path / "downloads/Main Test/"
        assert os.path.isdir(path)
    # Note: download_file is not used but is included to prevent
    # post-yield statement execution prematurely occurring
