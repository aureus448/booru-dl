"""
Constants for use in backend
"""
import configparser
import logging
import os
from typing import Tuple

logger = logging.getLogger(__file__)


def get_useragent() -> str:
    return "Booru DL"


def get_uri(ini: str = "uri.ini"):
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
    path = os.path.normpath(
        os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + f"/{ini}")
    )
    logger.debug(f"Path for Collecting URI config: {path}")
    parser = configparser.ConfigParser()
    parser.read(path)

    if "URI" in parser:
        uri = parser["URI"]["uri"]
        logger.info(f"URI Found: {uri}")
    else:
        logger.error("No URI Found - Please ensure uri.ini is set up correctly")
        raise ValueError
    return uri


def get_api_key(ini: str = "uri.ini") -> Tuple[str, str]:
    path = os.path.normpath(
        os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + f"/{ini}")
    )
    logger.debug(f"Path for Collecting URI config: {path}")
    parser = configparser.ConfigParser()
    parser.read(path)

    # If provided api key for booru - some require this
    if "api" in (parse := parser["URI"]) and "user" in parse:
        logger.info(
            "Collected API and Username from URI config - Will use for Authentication"
        )
        return parse["api"], parse["user"]
    else:
        logger.info("No API/Username found - Accepted behavior")
        return "", ""


def get_booru_data(main_uri: str) -> dict:
    """Given a URI provides a dictionary of expected booru website APIs

    Warnings:
        Doesn't check provided uri for accuracy at the moment

    Args:
        main_uri (str): URI to use as the main index for the website

    Returns:
        booru_data (dict): Dictionary of expected available URIs for a booru website
    """
    return dict(
        POST_URI=f"{main_uri}/posts.json",
        TAG_URI=f"{main_uri}/tags.json",
        ALIAS_URI=f"{main_uri}/tag_aliases.json",
    )


def main(debug: bool = True) -> dict:
    """Function run on execution of constants.py

    Provides some info on URI as well as the dict that was collected from the URI

    Warnings:
        Like the other functions indicate, URI is not checked for validity, meaning all
        following steps could be wrong

    Args:
        debug (bool): Whether to log (if ran as main, will do so)

    Returns:
        booru_data (dict): Dictionary of expected available URIs for a booru website
    """
    # Beginning of Script Execution
    if debug:
        logger.info("URI Check script started [1.0.0]")
    uri = get_uri()
    data = get_booru_data(uri)
    if debug:
        logger.debug(f"Booru Data: {data}")
    return data


if __name__ == "__main__":
    main()
