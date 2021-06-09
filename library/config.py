import configparser as parser
import logging
import os
from typing import Dict, List

logger = logging.getLogger(__file__)


class Section:
    """
    Enum-esque class containing expected data per-post
    """

    days = 0
    rating = 0
    min_score = 0
    min_favs = 0
    tags: list = []


class Config:
    """Configuration of booru settings

    Expects a config.ini file locally in order to work,
    however is able to create one if necessary
    """

    # Default values for config
    blacklist: List[str] = []
    default_days = 0
    default_rating = 0
    default_minscore = 0
    default_minfav = 0
    organize_by_type = False
    path = ""

    def __init__(self, ini: str = "config.ini"):
        path = os.path.normpath(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"\\{ini}"
        )  # goes up two directories lol
        self.path = path  # provide for use elsewhere
        self.config = parser.ConfigParser()
        if os.path.exists(path):
            self.config.read(path)
        else:
            logger.warning("No Config exists: Generating default")
            self.config = self.default_config(path)
        self.posts: Dict[str, Section] = dict()
        self.parse_config()

    def parse_config(self):
        for section in self.config.sections():
            section_check = section.lower()
            # print(section)
            # Go through all sections and get results
            if section_check == "default":
                self.default_days = int(self.attempt("days", section))
                self.default_rating = self.attempt("ratings", section)
                self.default_minscore = int(self.attempt("min_score", section))
                self.default_minfav = int(self.attempt("min_favs", section))

            elif section_check == "blacklist":
                self.blacklist = self.attempt("tags", section, [])

            elif section_check == "other":
                self.organize_by_type = self.attempt("organize_by_type", section)

            else:
                if section == "Example Post":
                    continue  # Skip example
                # Gets post attributes, uses defaults if unavailable
                self.posts[f"{section}"] = Section()
                self.posts[f"{section}"].name = f"{section}"
                self.posts[f"{section}"].days = int(
                    self.attempt("days", section, self.default_days)
                )
                self.posts[f"{section}"].rating = self.attempt(
                    "ratings", section, self.default_rating
                )
                self.posts[f"{section}"].min_score = int(
                    self.attempt("min_score", section, self.default_minscore)
                )
                self.posts[f"{section}"].min_favs = int(
                    self.attempt("min_favs", section, self.default_minfav)
                )
                self.posts[f"{section}"].tags = list(
                    map(str.strip, self.attempt("tags", section).split(","))
                )

    def attempt(self, var: str, section: str, failure=""):
        """Function that attempts to collect a variable from the dict

        Args:
            var (str): Key to search for
            section (str): Name of section to search for in posts
            failure (int): Return type provided by function

        Returns:
            variable or on failure an integer
        """ ""
        try:
            return self.config[section][var]
        except KeyError:
            logger.debug(
                f"Could not find key {var} in section {section}. Using default: {failure}"
            )
            return failure

    def default_config(self, ini: str):
        """Creates default config if config doesn't exist

        Returns:
            None
        """
        config = parser.ConfigParser()
        config["Default"] = {
            "days": "1",
            "ratings": "s",
            "min_score": "10",
            "min_favs": "0",
        }
        config["Blacklist"] = {"tags": "dog"}
        config["Other"] = {"organize_by_type": "False"}
        config["Example Post"] = {
            "notes": "Days can be any (reasonable) number, ratings include s for safe, q for questionable and e for "
            "explicit, tags can be any (valid) tag. Copy this format (without notes) and put what you need ("
            "don't forget to rename the [title])!",
            "days": "30",
            "ratings": "s",
            "min_score": "20",
            "min_favs": "0",
            "tags": "cat, cute",
        }
        with open(ini, "w") as cfg:
            config.write(cfg)
        return config
