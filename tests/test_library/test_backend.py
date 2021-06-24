import logging
import os

import pytest
import requests
from requests.sessions import Session

from booru_dl.library import backend, config


def test_set_logger():
    logger = logging.getLogger("Test Check")
    logger = backend.set_logger(logger, "booru-dl.log")
    assert type(logger) == logging.Logger


def test_get_session(collect_config):
    """Checks to make sure its the expected useragent and a proper session is created from it"""
    assert "Booru" in collect_config.useragent
    assert type(backend.get_session(collect_config.useragent)) == Session


@pytest.fixture
def package():
    return {
        "page": "b10000000",
        "limit": 320,  # Reminder: max limit of 320
        "tags": "",  # Reminder: hard limit of 4 tags
    }


def change_uri(URI, auth=False):
    collect_config = config.Config("test.ini")
    collect_config.parser["URI"]["uri"] = URI
    collect_config.uri = collect_config._get_uri()  # re-run uri collection
    collect_config.paths = collect_config._get_booru_data()
    if auth:
        collect_config.parser["URI"]["api"] = "test_api_key"
        collect_config.parser["URI"]["user"] = "test_user"
        (
            collect_config.api,
            collect_config.user,
        ) = collect_config._get_api_key()  # re-run api collection
    return collect_config


def test_request_uri_fail(get_session, package):
    """Provided an arbitrary package, see if requests succeed
    Runs through silent to ensure works
    """
    config = change_uri("https://google.com")
    with pytest.raises(requests.RequestException):
        backend.request_uri(
            get_session, config.paths["POST_URI"], package, auth=None, silent=True
        )


def test_request_uri_success(get_session, package):
    """Requires URI set in environment variables"""
    config = change_uri(os.environ["URI"])

    result = backend.request_uri(
        get_session, config.paths["POST_URI"], package, auth=None
    )
    assert result.status_code == 200


def test_request_uri_fail_authenticated(get_session, package):
    """Requires URI set in environment variables, will always 401 as I'm not willing to put my real keys"""
    config = change_uri(os.environ["URI"], auth=True)
    with pytest.raises(requests.RequestException):
        backend.request_uri(
            get_session,
            config.paths["POST_URI"],
            package,
            auth=(config.user, config.api),
        )


def test_request_uri_success_no_package(get_session):
    """Requires URI set in environment variables"""
    config = change_uri(os.environ["URI"])
    result = backend.request_uri(get_session, config.paths["POST_URI"], auth=None)
    assert result.status_code == 200


def test_cleanup(collect_config):
    """Just cleans up previous tests that used test.ini"""
    os.remove(collect_config.filepath)
    assert not os.path.exists(collect_config.filepath)
