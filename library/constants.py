"""
Constants for use in backend
"""
import configparser
import logging

from library import backend

logger = logging.getLogger("URI Check")


def get_uri(ini: str = "uri.ini") -> str:
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
    parser = configparser.ConfigParser()
    parser.read(ini)

    if "URI" in parser:
        uri = parser["URI"]["uri"]
        logger.info(f"URI Found: {uri}")
    else:
        logger.error("No URI Found - Please ensure uri.ini is set up correctly")
        raise ValueError
    return uri


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
        POST_URI=f"{main_uri}/post/show.json",
        INDEX_URI=f"{main_uri}/post/index.json",
        TAG_URI=f"{main_uri}/tag/index.json",
        ALIAS_URI=f"{main_uri}/tag_alias/index.json",
        TAG_SHOW_URI=f"{main_uri}/tag/show.json",
    )


if __name__ == "__main__":
    # Setup of Script Logger
    logger = backend.set_logger(logger, "booru-dl.log")

    # Beginning of Script Execution
    logger.info("URI Check script started [1.0.0]")

    uri = get_uri()
