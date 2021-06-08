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


def test_get_uri_fail():
    # Blank pass-through of config value will fail
    with pytest.raises(ValueError):
        constants.get_uri("")
