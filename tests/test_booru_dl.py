import os
import shutil

import pytest

import booru_dl

# import requests


# print("  SETUP otherarg", param)
# yield param
# print("  TEARDOWN otherarg", param)


@pytest.fixture(scope="module", params=os.environ["urls"].split(", "))
def create_config(request):
    conf_result = booru_dl.Config("test_main.ini")
    # Modify config with known failures to test
    # correct assumptions of a section
    conf_result.parser["Main Test/Correct_Section"] = {
        "days": "2000",
        "ratings": "s",
        "min_score": "500",
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

    conf_result.parser["URI"]["test_uri"] = request.param  # Required test field
    conf_result.uri = conf_result._get_uri()  # re-run uri collection
    conf_result.paths = conf_result._get_booru_data()  # re-run path collection
    conf_result._parse_config()  # re-run configuration
    with open(conf_result.filepath, "w") as cfg:
        conf_result.parser.write(cfg)
    yield conf_result
    os.remove(conf_result.filepath)


@pytest.fixture(scope="module")
def create_config_fast(create_config):
    """Limited form of create_config to run fast and run through (exist) code"""
    conf_result = booru_dl.Config("test_main_fast.ini")
    conf_result.parser["Main Test/Correct_Section"] = {
        "days": "30",
        "ratings": "s",
        "min_score": "1000",
        "tags": "cat",
    }
    conf_result.parser["URI"]["test_uri"] = create_config.uri["test_uri"][1]
    conf_result.uri = conf_result._get_uri()
    conf_result._parse_config()  # re-run configuration
    with open(conf_result.filepath, "w") as cfg:
        conf_result.parser.write(cfg)
    yield conf_result


# TODO requires fixing of _get_api_key
# @pytest.fixture(
#     params=[False, True],
#     ids=["Fake API [Force Program Crash]", "Real API [Download with API key]"],
# )
# def create_config_api(request, create_config):
#     correct_keys = request.param
#     if create_config.parser["URI"]["test_uri"] == os.environ['URI']:
#         if correct_keys:
#             create_config.parser["URI"]["test_uri"] = (
#                     create_config.parser["URI"]["test_uri"] + f',{os.environ["API"]}, {os.environ["USER"]}'
#             )
#         else:
#             create_config.parser["URI"]["test_uri"] = (
#                     create_config.parser["URI"]["test_uri"] + "test_api_key, test_user"
#             )
#         create_config.api, create_config.user = create_config._get_api_key()
#         with open(
#             create_config.filepath.name.replace("test_main.ini", "test_api.ini"), "w"
#         ) as cfg:
#             create_config.parser.write(cfg)
#         return create_config
#     else:
#         return None


@pytest.fixture(scope="module")
def download_file(create_config):
    result = booru_dl.Downloader("test_main.ini")
    yield result


@pytest.fixture(scope="module")
def download_file_exist(create_config_fast):
    result = booru_dl.Downloader("test_main_fast.ini")
    yield result


def test_download_files(download_file):
    download_file.get_data()
    path = download_file.path / "downloads/Main Test/"
    assert os.path.isdir(path)


def test_bad_download(download_file):
    """Sends a bad file to downloader"""
    if download_file.config.paths["test_uri"]:
        result = download_file.download_file(
            download_file.session,
            f'{download_file.config.paths["test_uri"]["POST_URI"]}/bad_download.png',
            "Bad Data",
            "bad_download",
        )
        assert result == -1
        path = download_file.path / "downloads/Bad Data/"
        assert os.path.isdir(path)
        shutil.rmtree(path)


def test_download_files_already_exist(download_file_exist):
    """Runs through "already exists" code paths
    Removes files afterward for next test
    """
    download_file_exist.get_data()
    path = download_file_exist.path / "downloads/Main Test/"
    assert os.path.isdir(path)


# TODO requires fixing of _get_api_key
# def test_download_files_api(download_file_exist, create_config_api):
#     """Uses the api, and forces a 401 error to occur - If it doesn't crash the test is a success"""
#     if create_config_api.user == "test_user":
#         with pytest.raises(requests.RequestException):
#             result = booru_dl.Downloader("test_api.ini")
#             result.get_data()
#     else:
#         result = booru_dl.Downloader("test_api.ini")
#         result.get_data()
#         path = result.path / "downloads/Main Test/"
#         assert os.path.isdir(path)
#     # Note: download_file is not used but is included to prevent
#     # post-yield statement execution prematurely occurring
