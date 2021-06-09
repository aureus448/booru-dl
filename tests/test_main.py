import logging
import os
import shutil

import main
from library import config

logger = logging.getLogger(__name__)


def test_download_files():
    conf_result = config.Config("test_main.ini")
    # Modify config with known failures to test
    conf_result.parser["Main Test"] = {
        "days": "2000",
        "ratings": "s",
        "min_score": "1000",
    }
    conf_result.parser["URI"]["uri"] = os.environ["URI"]

    with open(conf_result.filepath, "w") as cfg:
        conf_result.parser.write(cfg)

    result = main.Downloader("test_main.ini")
    path = os.path.normpath(result.path + "/downloads/Main Test/")
    assert os.path.isdir(path)
    os.remove(conf_result.filepath)  # removes created config file
    shutil.rmtree(path)  # removes test directory
