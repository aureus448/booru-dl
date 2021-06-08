import os

import pytest

from library import constants


def test_get_uri():
    # Ensures there is a uri.ini and make sure stuff exists
    if not os.path.exists("uri.ini"):
        file = open("uri.ini", "w+")
        file.write("[URI]\n")
        file.write("#Put URI Here\n")
        file.write("uri=apple.net\n")
        file.close()
    config = constants.get_uri()
    assert type(config) == str


def test_get_uri_exist():
    # Runs the previous test through second conditional (if file exists)
    test_get_uri()


def test_get_uri_fail():
    # Blank pass-through of config value will fail
    with pytest.raises(ValueError):
        constants.get_uri("")


def test_get_booru_data():
    # TODO come up with better tests and ensure it checks for validity of provided uri
    result = constants.get_booru_data("anything_works_here_at the moment")
    assert type(result) == dict


def test_main():
    result = constants.main()
    assert type(result) == dict
