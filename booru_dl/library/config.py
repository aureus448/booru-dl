# mypy: ignore-errors

import configparser
import logging
import os
import pathlib
from typing import Dict, List, Tuple

logger = logging.getLogger(__file__)


class Section:
    """
    Enum-esque class containing expected data per-post
    """

    name: str = ""
    days: int = 0
    rating: List[str] = []
    min_score: int = 0
    min_faves: int = 0
    tags: List[str] = []
    ignore_tags: List[str] = []
    allowed_types: List[str] = []


class Config:
    """Configuration of booru settings

    Expects a config.ini file locally in order to work,
    however is able to create one if necessary
    """

    # Default values for config
    path = os.path.dirname(__file__)  # path to provide to functions using this class
    blacklist: List[str] = []
    default_days: int = 0
    default_rating: List[str] = []
    default_min_score: int = 0
    default_min_fav: int = 0
    organize_by_type: bool = False
    posts: Dict[str, Section] = dict()

    def __init__(self, ini: str = "config.ini"):
        # Collect needed metadata
        self.parser = self._get_config(ini)
        self.useragent = self._get_useragent()
        self.uri = self._get_uri()
        self.api, self.user = self._get_api_key()
        self.paths = self._get_booru_data()

        # Create lists of data to collect
        self._parse_config()

    def _get_config(self, ini: str = "config.ini") -> configparser.ConfigParser:
        """Given config.ini collects the config to use

        Args:
            ini (str): Defaults to config.ini, file name to use for configuration
                Expected to be just the file name. DO NOT PASS AN ABSOLUTE PATH.

        Returns:
            parser (configparser.ConfigParser): Configuration file for project
        """
        path = pathlib.PurePath(f"{self.path}/../{ini}")
        self.filepath = os.path.abspath(path)
        logger.debug(f"Path for Collecting URI config: {path}")
        parser = configparser.ConfigParser()

        if os.path.exists(path):
            parser.read(path)
            return parser
        else:
            logger.warning("No Config exists: Generating default")
            return self._default_config(ini)

    def _get_useragent(self) -> str:
        if (
            "URI" in self.parser
            and "user" in self.parser["URI"]
            and self.parser["URI"]["user"]
        ):
            return f"Booru DL (user {self.parser['URI']['user']}"
        else:
            return "Booru DL (user unknown)"

    def _get_uri(self) -> str:
        """Given uri.ini collects the expected URI to use

        Expects a uri such as https://google.com (but a valid booru one)

        Warnings:
            No filtering or checking of the passed-through URI is done.
            If it is invalid, the rest of the code may fail prematurely.

        Args:
            ini (str): Defaults to uri.ini, file name to use for configuration

        Returns:
            uri (str): A URI to use
        """
        if "URI" in self.parser and "uri" in self.parser["URI"]:
            uri = self.parser["URI"]["uri"]
            logger.info(f"URI Found: {uri}")
        else:
            logger.error("No URI Found - Please ensure config is set up correctly")
            raise ValueError
        return uri

    def _get_api_key(self) -> Tuple[str, str]:
        # If provided api key for booru - some require this
        if "api" in (parse := self.parser["URI"]) and "user" in parse:
            logger.info(
                "Collected API and Username from URI config - Will use for Authentication"
            )
            return parse["api"], parse["user"]
        else:
            logger.info("No API/Username found - Accepted behavior")
            return "", ""

    def _get_booru_data(self) -> dict:
        """Given a URI provides a dictionary of expected booru website APIs

        Warnings:
            Doesn't check provided uri for accuracy at the moment

        Returns:
            booru_data (dict): Dictionary of expected available URIs for a booru website
        """

        return dict(
            POST_URI=f"{(main_uri := self.uri)}/posts.json",
            TAG_URI=f"{main_uri}/tags.json",
            ALIAS_URI=f"{main_uri}/tag_aliases.json",
        )

    def _parse_config(self):
        for section in self.parser.sections():
            section_check = section.lower()
            logger.debug(f"Working through section {section}")
            # Go through all sections and get results
            data = self.parser[section]

            if section_check == "default":
                # If data is missing defaults to:
                #   20 days
                #   rating of safe
                #   min score of 20
                #   min faves of 0
                #   allowed file extensions of jpg/png/gif (images only)
                self.default_days = int(data["days"]) if "days" in data else 20
                self.default_rating = data["ratings"] if "ratings" in data else ["s"]
                self.default_min_score = int(
                    data["min_score"] if "min_score" in data else 20
                )
                self.default_min_fav = int(
                    data["min_faves"] if "min_faves" in data else 0
                )
                self.default_allowed = (
                    data["allowed_types"]
                    if "allowed_types" in data
                    else "jpg, gif, png"
                )

            elif section_check == "blacklist":
                # Defaults to nothing blocked if doesn't exist
                self.blacklist = data["tags"].split(", ") if "tags" in data else []

            elif section_check == "other":
                # Allows for organizing files by datatype
                self.organize_by_type = (
                    data["organize_by_type"] if "organize_by_type" in data else False
                )

            else:
                # Skip example created by self.default_config or URI constants file
                if section == "Example Post" or section in ["URI", "INFO"]:
                    continue

                # Gets post attributes, uses defaults (see above) if unavailable
                self.posts[f"{section}"] = Section()
                self.posts[f"{section}"].name = f"{section}"
                self.posts[f"{section}"].days = int(
                    self.__get_key("days", section, self.default_days)
                )
                self.posts[f"{section}"].rating = self.__get_key(
                    "ratings", section, self.default_rating
                )
                self.posts[f"{section}"].min_score = int(
                    self.__get_key("min_score", section, self.default_min_score)
                )
                self.posts[f"{section}"].min_faves = int(
                    self.__get_key("min_faves", section, self.default_min_fav)
                )
                self.posts[f"{section}"].tags = list(
                    map(str.strip, (self.__get_key("tags", section, "")).split(","))
                )
                self.posts[f"{section}"].ignore_tags = list(
                    map(
                        str.strip,
                        (self.__get_key("ignore_tags", section, "")).split(","),
                    )
                )
                self.posts[f"{section}"].allowed_types = list(
                    map(
                        str.strip,
                        (
                            self.__get_key(
                                "allowed_types", section, self.default_allowed
                            )
                        ).split(","),
                    )
                )

    def __get_key(self, key: str, section: str, default: object):
        if key in (data := self.parser[section]):
            return data[key] if data[key] else default
        else:
            logger.warning(
                f"Missing data for {key} for section {section} [Set to Default of {default}]"
            )
            return default

    def _default_config(self, ini: str) -> configparser.ConfigParser:
        """Creates default config if config doesn't exist

        Returns:
            None
        """
        path = pathlib.PurePath(f"{self.path}/../{ini}")
        config = configparser.ConfigParser(allow_no_value=True)

        config["INFO"] = {
            "; booru-dl created by @aureus448": None,
            "???": "false",
        }
        config["URI"] = {
            "; Place the Booru URI here (a URI is like https://google.com)": None,
            "uri": "",
            "; [Optional] Support for a booru API key here": None,
            "api": "",
            "; [Optional] Support for a booru username here": None,
            "user": "",
        }
        config["Default"] = {
            "notes": "Default values used if missing for other sections. Set them to reasonable levels or your "
            "execution will not succeed",
            "days": "20",
            "ratings": "s",
            "min_score": "20",
            "min_faves": "0",
            "allowed_types": "jpg, png, gif",
        }
        config["Blacklist"] = {
            "; Hide stuff you don't want, in this example canines": None,
            "tags": "canine",
        }
        config["Other"] = {
            "; Organize by file extension into subfolders [Not working at the moment]": None,
            "organize_by_type": "False",
        }
        config["Example Post"] = {
            "; Copy this format (without or without comments [;]) and put what you need": None,
            "; Don't forget to rename the [title]!": None,
            "; Days can be any number (Be reasonable or you'll be stuck for hours)": None,
            "days": "30",
            "; ratings include s for safe, q for questionable and e for explicit": None,
            "ratings": "s",
            "min_score": "20",
            "min_faves": "0",
            "tags": "cat, cute",
            "; Per-section allowed extension types (gif, webm, png etc. different from default)"
            " [Include all or leave blank]": None,
            "allowed_types": "",
            "; ignore_tags indicate tags to ignore from blacklist (canine used in this example, "
            "will allow any post with canines to come through)": None,
            "ignore_tags": "canine",
            "; blacklist_tags indicate tags to add to blacklist [For just the section] "
            "(canine used in this example, will disallow any post with canine to come through)": None,
            "blacklist_tags": "canine",
        }
        with open(path, "w") as cfg:
            config.write(cfg)
        return config


if __name__ == "__main__":
    # Intended to be used with debug breakpoints - otherwise do not use
    config = Config("test.ini")
    # Warning: Make sure config is passed a test value or you could accidentally delete your config
    os.remove(config.filepath)
