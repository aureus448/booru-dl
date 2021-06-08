import os

import pytest

import main


@pytest.fixture(scope="module")
def make_uri():
    """Creates the real URI for use in main test code via workflow"""
    path = os.path.normpath(
        os.path.dirname(os.path.abspath(main.__file__)) + "/library/uri.ini"
    )
    print(f"Path for Make URI: {path}")
    if not os.path.exists(path):
        print("Made file")
        file = open(path, "w+")
        file.write("[URI]\n")
        file.write("#Put URI Here\n")
        print(f"Environment Variable for URI: {os.environ['URI']}")
        file.write(f"uri={os.environ['URI']}\n")
        file.close()
        with open(path) as file:
            print(file.readlines())
