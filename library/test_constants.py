import logging
import os

import pytest

from library import constants

logger = logging.getLogger(__name__)


def test_get_uri(delete: bool = False):
    # Ensures there is a uri.ini and make sure stuff exists
    logger.debug(f"Path for Test URI: {os.path.abspath('test.ini')}")
    if not os.path.exists("test.ini"):
        file = open("test.ini", "w+")
        file.write("[URI]\n")
        file.write("#Put URI Here\n")
        file.write("uri=apple.net\n")
        file.close()
    config = constants.get_uri("test.ini")
    if delete:
        os.remove("test.ini")  # delete after test run successful
    assert type(config) == str


def test_get_uri_exist():
    # Runs the previous test through second conditional (if file exists)
    test_get_uri(delete=True)  # deletes file after successful run


def test_get_uri_fail():
    # Blank pass-through of config value will fail
    with pytest.raises(ValueError):
        constants.get_uri("")


def test_get_booru_data():
    # TODO come up with better tests and ensure it checks for validity of provided uri
    result = constants.get_booru_data("anything_works_here_at the moment")
    assert type(result) == dict


def test_main():
    result = constants.main(debug=False)
    assert type(result) == dict


def test_get_useragent():
    assert type(constants.get_useragent()) == str
