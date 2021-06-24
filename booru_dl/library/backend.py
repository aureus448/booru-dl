"""Backend for booru access via requests

Primarily used to POST request the booru website, collect a Requests session, and setup logging for all files.
"""
import logging
import typing

import requests

logger = logging.getLogger(__file__)


def get_session(useragent: str) -> requests.Session:
    """Offers a Session for requests

    Args:
        useragent (str): Name to use for user-agent when requesting of booru website.
            Defaults to ``Booru DL (user unknown)`` if no user_name provided

    Returns:
        requests.Session: Requests Session object with correctly formatted user-agent
    """
    session = requests.Session()
    session.headers.update({"User-Agent": useragent})
    return session


# def tag_alias(session, user_tag):
#     """This function is WIP
#
#     Goal is to take given tags and ensure they exist and alias properly
#
#     TODO convert constants usage to new formats
#     """
#     prefix = ""
#
#     # Cannot check : tags for validity
#     if ":" in user_tag:
#         if constants.DEBUG:
#             print("Impossible to check tag {}.".format(user_tag))
#         return user_tag
#
#     # Remove any optional flags from the tag, for now
#     if user_tag[0] == "~":
#         prefix = "~"
#         user_tag = user_tag[1:]
#
#     elif user_tag[0] == "-":
#         prefix = "-"
#         user_tag = user_tag[1:]
#
#     payload = {"name": user_tag}
#     start_time = time.time()
#     result = request_uri(session, constants.TAG_URI, payload)
#     # Ensure proper timing to comply with API limit
#     timer(start_time, "Tag Check")
#
#     # Error when looking for tag
#     if isinstance(result, int):
#         return False
#
#     results = result.json()
#
#     # Wildcards are immediately valid
#     if "*" in user_tag and results:
#         if constants.DEBUG:
#             print("Tag {} is valid.".format(user_tag))
#         return user_tag
#
#     # Check for tag within tag list
#     for tag in results:
#         if user_tag == tag["name"]:
#             if constants.DEBUG:
#                 print("Tag {} is valid.".format(user_tag))
#             return prefix + user_tag
#
#     # Reaching here means check for tag aliases
#     # This code would be much smaller if the API allowed a search by tag alias and returned the proper tag
#     start_time = time.time()
#     payload = {"approved": "true", "query": user_tag}
#     result = request_uri(session, constants.ALIAS_URI, payload)
#
#     # Error when looking for tag alias
#     if isinstance(result, int):
#         return False
#
#     results = result.json()
#
#     for tag in results:
#         # If found the tag (look up its alias)
#         if user_tag == tag["name"]:
#             payload = {"id": tag["alias_id"]}
#             result = request_uri(session, constants.TAG_SHOW_URI, payload)
#
#             # Error when trying to show tag
#             if isinstance(result, int):
#                 return False
#
#             results = result.json()
#
#             print("Tag {0} was changed to {1}".format(user_tag, results["name"]))
#             timer(start_time, "Tag Alias")
#             return prefix + results["name"]
#
#     print(f"The tag {0} is spelled incorrectly or does not exist.".format(user_tag))
#     return False
#     pass


def request_uri(
    session: requests.Session,
    url: str,
    package: typing.Dict[str, object] = None,
    auth: typing.Tuple[str, str] = None,
    silent: bool = False,
) -> requests.Response:
    """POST requests a given booru website for data

    Args:
        session (requests.Session): Session to use in POST requesting website
        url (str): URL to request data from
        package (dict): Dictionary containing data to send to URL
        auth (tuple): Tuple containing api_key and user_name if provided
        silent (bool): Whether to provide log data silently (DEBUG level) or notify of errors (ERROR level)

    Returns:
        object: Error code if failure or data if successful
    """
    if package and auth:
        result = session.get(url, params=package, auth=auth)
    elif package:
        result = session.get(url, params=package)
    else:
        result = session.get(url)
    # print(result.url)

    if result.status_code == 200:
        return result
    else:
        if not silent:
            logger.error(
                "Request for {0} failed. Error code {1}".format(url, result.status_code)
            )
        else:
            logger.debug(
                "Request for {0} failed. Error code {1}".format(url, result.status_code)
            )
        raise requests.RequestException(result.status_code)


# def timer(start_time, name="URI Request", optional_clarifier=""):
#     """Defines total time for function based on a start_time and optional naming"""
#     end_time = time.time()
#
#     # Time in ms for function call
#     total_time = (end_time - start_time) * 1000
#
#     if constants.TIMING:
#         if optional_clarifier:
#             print(
#                 "TIMING: {0} for {1} took {2:0.3f}ms".format(
#                     name, optional_clarifier, total_time
#                 )
#             )
#         else:
#             print("TIMING: {0} took {1:0.3f}ms".format(name, total_time))
#
#     # Warning Based on booru's API Rate Limit of 2 requests a second
#     if total_time < 500:
#         sleep_time = 500 - total_time
#         if constants.TIMING:
#             logger.warning(
#                 "Error! Faster than API Limit: Waiting {0:0.3f} ms for next function call".format(
#                     sleep_time
#                 )
#             )
#         time.sleep(sleep_time / 1000)


def set_logger(log: logging.Logger, name: str) -> logging.Logger:
    """Set up of logging program based on a provided logging.Logger

    Args:
        log (logging.Logger): Logger object to add handlers to
        name (str): Output file name

    Returns:
        logging.Logger: Logger formatted with log format specified (by me)
    """
    log.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    fh = logging.FileHandler(name, mode="w")
    sh.setLevel(logging.INFO)
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%d/%m/%Y | %H:%M:%S"
    )
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)

    log.addHandler(fh)
    log.addHandler(sh)
    return log
