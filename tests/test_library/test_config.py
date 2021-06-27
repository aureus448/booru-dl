import configparser
import os

import pytest

from booru_dl.library import config

# Example
# @pytest.mark.parametrize("test_input,expected", [("3+5", 8), ("2+4", 6), ("6*9", 42)])
# def test_eval(test_input, expected):
#     assert eval(test_input) == expected


def test__get_config(collect_config):
    """Ensure config was produced correctly"""
    parser = collect_config
    assert (
        type(parser) == config.Config
        and type(parser.parser) == configparser.ConfigParser
    )


def test__get_useragent_unknown(collect_config):
    """Check Useragent is unknown"""
    assert "unknown" in collect_config.useragent


def test__get_useragent_provided_username(collect_config):
    """Check Useragent was collected properly"""
    collect_config.parser["URI"]["api"] = "test_api_key"
    collect_config.parser["URI"]["user"] = "test_user"
    (
        collect_config.api,
        collect_config.user,
    ) = collect_config._get_api_key()  # re-run api collection
    collect_config.useragent = collect_config._get_useragent()
    assert "test_user" in collect_config.useragent


@pytest.mark.parametrize(
    "test_urls, run_all",
    zip(os.environ["urls"].split(", "), [True, False, False, False, False]),
)
def test__get_uri(test_urls, run_all, collect_config):
    """Tests the config ability to collect available uris"""
    collect_config.parser["URI"]["test_0"] = f"{test_urls}"
    if run_all:
        collect_config.parser["URI"]["test_1"] = f"{test_urls}, ,test_user"
        collect_config.parser["URI"]["test_2"] = f"{test_urls},, test_user, test_api"
        collect_config.parser["URI"][
            "test_3"
        ] = ""  # Should produce warning of missing data
        collect_config.parser["URI"]["test_4"] = f"{test_urls}"
        collect_config.parser["URI"]["test_5"] = f"{test_urls}"
    collect_config.uri = collect_config._get_uri()  # re-run uri collection
    assert type(collect_config.uri) == dict
    assert type(collect_config.uri["test_0"]) == list
    assert collect_config.uri["test_0"][2] in ["danbooru", "gelbooru", "None"]


def test__get_uri_fail_on_missing(collect_config):
    """Force set URI to fail"""
    with pytest.raises(ValueError):
        # replace dict with one that doesn't include uri
        del collect_config.parser["URI"]
        collect_config.uri = collect_config._get_uri()  # re-run uri collection


def test__get_api_key(collect_config):
    """Force set API key and user to something to see if collection is correct"""
    collect_config.parser["URI"]["api"] = "test_api_key"
    collect_config.parser["URI"]["user"] = "test_user"
    (
        collect_config.api,
        collect_config.user,
    ) = collect_config._get_api_key()  # re-run api collection
    assert collect_config.api == "test_api_key" and collect_config.user == "test_user"


def test__get_api_key_missing_config(collect_config):
    """API key and User key missing (Either or, both are needed or code path skips)"""
    collect_config.parser["URI"] = {"uri": "code_crasher"}
    (
        collect_config.api,
        collect_config.user,
    ) = collect_config._get_api_key()  # re-run api collection
    assert not collect_config.api and not collect_config.user


def test__get_booru_data(collect_config):
    """Changes the uri and sees if it propagates properly to booru data"""
    test_urls = os.environ["urls"].split(", ")
    collect_config.parser["URI"]["test_uri"] = (main_uri := f"{test_urls[0]}")
    collect_config.uri = collect_config._get_uri()  # re-run uri collection
    collect_config.paths = collect_config._get_booru_data()  # re-run path collection
    expected = dict(
        POST_URI=f"{main_uri}/posts.json",
        TAG_URI=f"{main_uri}/tags.json",
        ALIAS_URI=f"{main_uri}/tag_aliases.json",
    )
    assert str(expected.values()) == str(collect_config.paths["test_uri"].values())


def test__parse_config(collect_config):
    """Adds an entirely new section to ensure code runs"""
    collect_config.parser["NEW_SECTION"] = {
        "days": "300",
        "ratings": "s",
        "min_score": "201",
        "min_faves": "1",
        "tags": "pikachu, cute",
    }
    collect_config._parse_config()  # force re-parse of config file
    assert "NEW_SECTION" in collect_config.posts
    assert collect_config.posts["NEW_SECTION"].tags == ["pikachu", "cute"]


def test__parse_config_changed_default(collect_config):
    """Changes defaults and checks if the change is correctly set to new section"""
    collect_config.parser["Default"] = {
        "min_faves": "40",
    }
    collect_config.parser["NEW_SECTION_2"] = {
        "days": "300",
        "ratings": "s",
        "min_score": "201",
        "tags": "pikachu, cute",
    }
    collect_config._parse_config()  # force re-parse of config file
    assert collect_config.default_min_fav == 40
    assert collect_config.posts["NEW_SECTION_2"].min_faves == 40


def test__default_config():
    """Create a completely new default config using the default config path"""
    result = config.Config("new_fake_ini.ini")
    assert "new_fake_ini.ini" in result.filepath.name
    os.remove(result.filepath)  # clean up


def test_cleanup(collect_config):
    """Just cleans up previous tests that used the test.ini"""
    os.remove(collect_config.filepath)
    assert not os.path.exists(collect_config.filepath)
