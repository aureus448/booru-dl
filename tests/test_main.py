import logging
import os
import shutil

import main
from library import config

logger = logging.getLogger(__name__)


def test_download_files(make_uri):
    conf_result = config.Config("test_main.ini")
    # Modify config with known failures to test
    conf_result.config["Main Test"] = {
        "days": "2000",
        "ratings": "s",
        "min_score": "1000",
    }
    with open(conf_result.path, "w") as cfg:
        conf_result.config.write(cfg)

    result = main.Downloader("test_main.ini")
    path = os.path.normpath(result.path + "/downloads/Main Test")
    assert os.path.exists(path)
    os.remove(conf_result.path)  # removes created config file
    shutil.rmtree(path)  # removes test directory
