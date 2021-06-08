import os
import shutil

import main
from library import config


def test_download_files():
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
    path = os.path.dirname(os.path.abspath(__file__)) + "\\downloads\\Main Test"
    assert os.path.exists(path)
    os.remove(result.path)  # removes created config file
    shutil.rmtree(path)  # removes test directory
