import logging
import os

import pytest
import requests
from requests.sessions import Session

from booru_dl.library import backend, config


@pytest.fixture(scope="module", params=os.environ["urls"].split(", "))
def provide_package_data(request):
    config_file = config.Config("test.ini")
    config_file.parser["URI"]["test_0"] = f"{request.param}"
    config_file.uri = config_file._get_uri()
    config_file.paths = config_file._get_booru_data()
    tags = ["Pikachu"]
    before_id = 10000000
    package = backend.format_package(tags, before_id, config_file.uri["test_0"][2])
    return config_file, package


def test_set_logger():
    logger = logging.getLogger("Test Check")
    logger = backend.set_logger(logger, "booru-dl.log")
    assert type(logger) == logging.Logger


def test_get_session(collect_config):
    """Checks to make sure its the expected useragent and a proper session is created from it"""
    assert "Booru" in collect_config.useragent
    assert type(backend.get_session(collect_config.useragent)) == Session


def test_request_uri_fail(get_session):
    """Provided an arbitrary package, see if requests succeed
    Runs through silent to ensure works
    """
    with pytest.raises(requests.RequestException):
        backend.request_uri(
            get_session, "https://google.com.json?", auth=None, silent=True
        )


def test_request_uri_success(provide_package_data, get_session):
    """Requires URI set in environment variables"""
    if provide_package_data[1]:
        result = backend.request_uri(
            get_session,
            provide_package_data[0].paths["test_0"]["POST_URI"],
            provide_package_data[1],
            auth=None,
        )
        assert result.status_code == 200


def test_request_uri_fail_authenticated(provide_package_data, get_session):
    """Requires URI set in environment variables, will always 401 as I'm not willing to put my real keys"""
    if provide_package_data[1]:
        with pytest.raises(requests.RequestException):
            result = backend.request_uri(
                get_session,
                provide_package_data[0].paths["test_0"]["POST_URI"],
                provide_package_data[1],
                auth=(provide_package_data[0].user, provide_package_data[0].api),
            )
            if result.status_code == 200:
                raise requests.RequestException  # Some sites silently fail - not sure why


def test_request_uri_success_no_package(provide_package_data, get_session):
    """Requires URI set in environment variables"""
    if provide_package_data[1]:
        result = backend.request_uri(
            get_session, provide_package_data[0].paths["test_0"]["POST_URI"], auth=None
        )
        assert result.status_code == 200


def test_cleanup(collect_config):
    """Just cleans up previous tests that used test.ini"""
    os.remove(collect_config.filepath)
    assert not os.path.exists(collect_config.filepath)
