import os

from library import config

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "\\test.ini"


def test_config_no_exist():
    result = config.Config("test.ini")
    assert type(result) == config.Config  # check if it loaded correctly


def test_config_build_modify():
    # Modifies the config "test.ini" with known failures for later tests
    result = config.Config("test.ini")  # load config created in previous
    # Modify config with known failures to test
    result.config["Failure Post"] = {
        "notes": "Days can be any (reasonable) number, ratings include s for safe, q for questionable and e for "
        "explicit, tags can be any (valid) tag. Copy this format (without notes) and put what you need ("
        "don't forget to rename the [title])!",
        # No days provided
        "ratings": "s",
        "min_score": "20",
        # No favs provided
        "tags": "cat, cute",
    }

    with open(path, "w") as cfg:
        result.config.write(cfg)

    assert result.blacklist == "dog"


def test_config_known_attempt_err():
    # Guarantee attempt() function worked and set days to 1 despite 'days' key not existing in Failure Post
    result = config.Config("test.ini")  # reload config created in previous
    assert (
        result.posts["Failure Post"].days == 1
        and "days" not in result.config["Failure Post"]
    )
    os.remove(path)  # remove test.ini created file for next test runs
