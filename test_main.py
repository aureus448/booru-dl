import logging
import os
import shutil

import main
from library import config

logger = logging.getLogger(__name__)


def make_uri():
    """Creates the real URI for use in main test code via workflow"""
    path = os.path.normpath(os.path.abspath("library/uri.ini"))
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


def test_download_files():
    make_uri()
    result = config.Config("test_main.ini")
    # Modify config with known failures to test
    result.config["Main Test"] = {
        "days": "2000",
        "ratings": "s",
        "min_score": "1000",
    }
    with open(result.path, "w") as cfg:
        result.config.write(cfg)

    main.Downloader("test_main.ini")
    path = os.path.normpath(
        os.path.dirname(os.path.abspath(__file__)) + "/downloads/Main Test"
    )
    assert os.path.exists(path)
    os.remove(result.path)  # removes created config file
    shutil.rmtree(path)  # removes test directory
