"""Collects a provided configuration and provides parsing of data collected

A default configuration will be created on first run if none is provided.
A configuration file is required to have the following data sections/fields:

#. URI
    * uri: URL/URI of booru website (Ex. https://google.com)
    * ``OPTIONAL`` api: API key for the booru website
    * ``SEMI-OPTIONAL`` user: Username for the booru website

#. Default
    * ``OPTIONAL`` days: Default amount of days to search for
    * ``OPTIONAL`` ratings: Default rating(s) to search for
    * ``OPTIONAL`` min_score: Default minimum score for each post
    * ``OPTIONAL`` min_favs: Default minimum favorites for each post
    * ``OPTIONAL`` allowed_types: Default allowed filetypes for all sections

#. Other
    * ``OPTIONAL`` organize_by_type: Whether files should be organized by filetype in each section

        Example: For section ``Dog``, gifs will go into a ``Dog/gif`` sub-folder

#. Blacklist
    * ``OPTIONAL`` tags: list of tags to ignore

        Example: ``cat`` - what a disgusting creature

#. <Sections to Search #1 -> #n>
    If data is missing for any field other than tag, the data is collected from the
    default provided in the configuration file.

    * tags: Tags to search for the section
    * ``OPTIONAL`` days:  days to search for section
    * ``OPTIONAL`` ratings: ratings to search for section
    * ``OPTIONAL`` min_score: minimum score to search for in a section
    * ``OPTIONAL`` ignore_tags: Tags to ignore for this specific section

        Example: ``cat`` in blacklist and ignore_tags means for this specific section ``cat`` is allowed

    * ``OPTIONAL`` allowed_types: List of filetypes to allow for a specific section

Note:
    Attributes that are listed as ``OPTIONAL`` mean that the code is designed to auto-fill these fields with
    appropriate data where missing. Anything not listed as ``OPTIONAL`` is therefore required to prevent the code
    from crashing and/or unexpected code behavior.

    For example, when data is missing for defaults, the [Default] section is set to::

        [Default]
        days = 20
        ratings = s
        min_score = 20
        min_faves = 0
        allowed_types = jpg, gif, png

    And in this vein, missing section data is set to the defaults values either provided above or in the config.
"""
# mypy: ignore-errors

import configparser
import logging
import os
import pathlib
from typing import Dict, List, Tuple

# TODO modify URI grabbing to support following structure:
#  [URI]
#  uri = uri_1, uri_2
#  uri_1 = api_key, user_name, booru_type
#  allows for modular amount of URIs to search
#  booru_type is especially important for determining codepaths - allow for auto-determination,
#    but ADD DIRECTLY TO file once type is known [Requires rewrite to disk of config - potentially dangerous]
#  Or: in [URI] each field is <uri_nickname> with data being <uri_url>, <api_key>, <user_name>

# TODO modify Section to determine which API endpoints are allowed to be searched
#  [Section_foo]
#  <data>
#  api = uri_1, uri_2 (defined exactly like in URI [allow nickname? how to support])


class Section:
    """Class containing filtering data for use in search and collection"""

    name: str  #: Name of section (Ex. ``Dog``)
    days: int  #: Days to search for on booru
    rating: List[str]  #: Rating(s) to search for
    min_score: int  #: Minimum score of section posts
    min_faves: int  #: Minimum favorites of section posts
    tags: List[str]  #: Tags for section posts
    ignore_tags: List[
        str
    ]  #: Tags to ignore for this specific section (Allows skipping blacklist)
    allowed_types: List[
        str
    ]  #: List of file types allowed per section (Allows changing file-types per section)
    api_endpoint: List[str]  #: Allowed APIs to use based on [URI] key


class Config:
    """Configuration of booru settings

    Expects a ``config.ini`` file in a directory above the file in order to work,
    however is able to create one if necessary

    Note:
        ``config.ini`` (or any provided config using the ``ini`` attribute) is
        collected from the parent directory from the ``Config()`` class. What this
        means is if the ``config.py`` file is located as follows::

            /                   - Project Root
            /library/config.py  - Location of config.py
            /main.py            - Location of main.py
            /*.ini              - Location of ini collected (Where * is name provided in ini attribute)

    """

    # Default values for config
    blacklist: List[
        str
    ]  #: Blacklist attribute containing all tags to ignore on booru posts
    default_days: int  #: Default amount of days to check
    default_rating: List[str]  #: Default rating of posts on the booru site
    default_min_score: int  #: Default minimum score of posts on the booru site
    default_min_fav: int  #: Default minimum favorite amount of posts on the booru site
    organize_by_type: bool  #: Whether to organize file types within specific sub-folders
    posts: Dict[
        str, Section
    ] = dict()  #: Dictionary of all sections to search for within the given config

    def __init__(self, ini: str):
        self.filepath: pathlib.PurePath = pathlib.PurePath(ini)
        self.path: pathlib.PurePath = self.filepath.parent

        # Setup logging

        logging.debug(f"Config Root path: {os.path.abspath(self.path)}")
        logging.debug("Note: Above should be same as Root path")
        logging.debug(f"Config ini path: {os.path.abspath(self.filepath)}")

        # Collect needed metadata
        self.parser = self._get_config()
        self.useragent = self._get_useragent()
        self.uri = self._get_uri()
        self.api, self.user = self._get_api_key()
        self.paths = self._get_booru_data()

        # Create lists of data to collect
        self._parse_config()

    def _get_config(self) -> configparser.ConfigParser:
        """Collects the config to use using class attributes

        Returns:
            configparser.ConfigParser: Configuration file for project
        """
        logging.debug(f"Path for Collecting URI config: {self.filepath}")
        parser = configparser.ConfigParser()

        if os.path.exists(self.filepath):
            parser.read(self.filepath)
            return parser
        else:
            logging.warning("No Config exists: Generating default")
            logging.warning("Please re-run the program after filling in config data")
            return self._default_config()

    def _get_useragent(self) -> str:
        """Creates a useragent string for use

        Returns:
            str: Useragent to be provided during POST requests
        """
        if (
            "URI" in self.parser
            and "user" in self.parser["URI"]
            and self.parser["URI"]["user"]
        ):
            return f"Booru DL (user {self.parser['URI']['user']}"
        else:
            return "Booru DL (user unknown)"

    def _get_uri(self) -> Dict[str, list]:
        """Given uri.ini collects the expected URI to use

        Expects a uri such as https://google.com (but a valid booru one)

        Warnings:
            No filtering or checking of the passed-through URI is done.
            If it is invalid, the rest of the code may fail prematurely.

        Args:
            ini (str): Defaults to uri.ini, file name to use for configuration

        Returns:
            list: List of URI Nicknames, URIs, User Names, and API keys if data exists
        """
        if "URI" in self.parser:
            """
            Warning: This whole section uses list comprehension and may be confusing

            The basics of what this does: if data exists, add it to a list

            For uris, user_name, and api_keys, it checks data exists and then adds it to the list
            otherwise it will insert '' to indicate the data doesn't exist for that specific uri
            """
            uri_section = self.parser["URI"]
            available_uri = [key for key in uri_section.keys()]
            uri_data = [[uri, uri_section[uri]] for uri in available_uri]

            # Setup list
            result_list: Dict[str, list] = {}

            # Collect URI data
            for data in uri_data:
                if data[1] is None:  # NoneType
                    continue
                if (
                    len((result := list(map(str.strip, data[1].split(","))))) > 2
                ):  # URI, username and api_key exists
                    logging.debug(f"URI Found: {result[0]}")
                    logging.debug(f"USER NAME Found for {result[0]}")
                    logging.debug(f"API KEY Found for {result[0]}")
                    result_list[data[0]] = [data[0], result[0], result[1], result[2]]
                elif len(result) > 1:  # URI and username exists
                    logging.debug(f"URI Found: {result[0]}")
                    logging.debug(f"USER NAME Found for {result[0]}")
                    logging.debug(f"API KEY N/A for {result[0]}")
                    result_list[data[0]] = [data[0], result[0], result[1], ""]
                elif (
                    len(result) > 0 and result[0] != ""
                ):  # URI exist, all other data missing
                    logging.debug(f"URI Found: {result[0]}")
                    logging.debug(f"USER NAME N/A for {result[0]}")
                    logging.debug(f"API KEY N/A for {result[0]}")
                    result_list[data[0]] = [data[0], result[0], "", ""]
                else:
                    logging.warning(
                        f"Found broken key {data[0]} in [URI] - Please fix or remove."
                    )
        else:
            logging.error(
                "No URI Section Found - Please ensure config is set up correctly"
            )
            logging.error(
                "Possible Solution: Delete config and allow program to create new one"
            )
            raise ValueError
        return result_list

    def _get_api_key(self) -> Tuple[str, str]:
        """Collects the api and username for use in POST requests if provided


        Returns:
            Tuple[str, str]: A tuple containing ``(api_key, user_name)`` or ``('','')`` if undefined
        """
        # If provided api key for booru - some require this
        if "api" in (parse := self.parser["URI"]) and "user" in parse:
            logging.debug(
                "Collected API and Username from URI config - Will use for Authentication"
            )
            return parse["api"], parse["user"]
        else:
            logging.debug("No API/Username found - Accepted behavior")
            return "", ""

    def _get_booru_data(self) -> Dict[str, dict]:
        """Given a URI provides a dictionary of expected booru website APIs

        Warnings:
            Doesn't check provided uri for accuracy at the moment

        Returns:
            Dict[str, str]: Dictionary of *expected* available URIs for a booru website

        Note:
            URIs available per booru is different, this contains a basic setup based on guesses.
            Failure to collect URIs properly should be submitted to the dev for future improvement.
        """
        booru_endpoints: Dict[str, dict] = {}
        for uri in self.uri:
            # uri is a list containing: [nickname, url, username, api]
            booru_endpoints[uri] = dict(
                POST_URI=f"{(main_uri := self.uri[uri][1])}/posts.json",
                TAG_URI=f"{main_uri}/tags.json",
                ALIAS_URI=f"{main_uri}/tag_aliases.json",
            )
        return booru_endpoints

    def _parse_config(self) -> None:
        """Parses the config provided by ``__init__()`` for sections to search

        Also collects and determines defaults, blacklist, and any special fields per-section as needed.

        Note:
            See module documentation for a full list of available fields.

        Returns:
            None
        """
        for section in self.parser.sections():
            section_check = section.lower()
            logging.debug(f"Working through section {section}")
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
                    self.__get_key("days", section, self.default_days.__str__())
                )
                self.posts[f"{section}"].rating = self.__get_key(
                    "ratings", section, self.default_rating.__str__()
                )
                self.posts[f"{section}"].min_score = int(
                    self.__get_key(
                        "min_score", section, self.default_min_score.__str__()
                    )
                )
                self.posts[f"{section}"].min_faves = int(
                    self.__get_key("min_faves", section, self.default_min_fav.__str__())
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

    def __get_key(self, key: str, section: str, default: str) -> str:
        """Collects data from the ``configparser.Configparser`` class if available, or returns default value

        Args:
            key (str): Key to search for in config dictionary
            section (str): Section name (provided to indicate errors in ``logging``)
            default (object): Default state of requested value

        Returns:
            object: Value for section if found or default if missing
        """
        if key in (data := self.parser[section]):
            return data[key] if data[key] else default
        else:
            logging.warning(
                f"Missing data for {key} for section {section} [Set to Default of {default}]"
            )
            return default

    def _default_config(self) -> configparser.ConfigParser:
        """Creates default config if config doesn't exist

        Uses class attributes to determine filename

        Returns:
            configparser.ConfigParser: A created default configuration with included comments
            for user understanding of options available
        """
        config = configparser.ConfigParser(allow_no_value=True)

        config["INFO"] = {
            "; booru-dl created by @aureus448": None,
            "???": "false",
        }
        config["URI"] = {
            "; Place the Booru data here in this order: url, username [Optional], api_key [Optional]": None,
            "insert_nickname_for_uri": "",
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
        with open(self.filepath, "w") as cfg:
            config.write(cfg)
        return config


if __name__ == "__main__":
    # Intended to be used with debug breakpoints - otherwise do not use
    config = Config("../config.ini")
    # Warning: Make sure config is passed a test value or you could accidentally delete your config
    os.remove(config.filepath)
