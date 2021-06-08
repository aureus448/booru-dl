"""
Constants for use in backend
"""
import configparser
import logging

from library import backend

logger = logging.getLogger("URI Check")


def get_uri() -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read("uri.ini")
    return parser


if __name__ == "__main__":
    # Setup of Script Logger
    logger = backend.set_logger(logger, "booru-dl.log")

    # Beginning of Script Execution
    logger.info("URI Check script started [1.0.0]")

    config = get_uri()

    if "URI" in config:
        logger.info(f"URI Found: {config['URI']['uri']}")
    else:
        logger.error("No URI Found - Please ensure uri.ini is set up correctly")
