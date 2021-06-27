"""Backend for booru access via requests

Primarily used to POST request the booru website, collect a Requests session, and setup logging for all files.
"""
import logging
import typing

import cloudscraper
import requests

# TODO refactor backend into its own class
#  Allows for multiple backend sessions to be used in main file
#    this change is necessary to support multiple uris

# TODO add backend support for API endpoint determination per URI
#   some boorus are different, would be nice to create modularized code
#   to work with the majority of available boorus - TBD

# TODO fix Downloader() class in main having its own version of request_uri for download_file()


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
            logging.error(
                "Request for {0} failed. Error code {1}".format(url, result.status_code)
            )
        else:
            logging.debug(
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
#             logging.warning(
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


def determine_api(api: str) -> str:
    """Function that attempts to determine the API for a given site.

    Args:
        api (str): URL of the site (Such as https://google.com)

    Returns:
        str: Determined API endpoint type for the given site, or 'None' if couldn't determine
    """
    api_type = "None"  # Default value if all try-except fail

    tags = ["Pikachu"]  # attempts to get a pikachu picture from each website
    before_id = 1000000  # attempts to collect latest with arbitrarily high value
    session = get_session("Test_API_ENDPOINT")

    # Attempt 'danbooru' booru api setup
    try:
        package = format_package(tags, before_id, "danbooru")
        result = session.get(api + "/posts.json", params=package)
        if result.status_code == 200:
            data = result.json()
            if len(data) == 1:
                try:
                    data = data["posts"]
                except ValueError:
                    pass
            if type(data) == list and type(data[0]) == dict:
                api_type = "danbooru"
        else:
            raise requests.RequestException(f"Error Status Code: {result.status_code}")
    except Exception as e:
        if type(e) != requests.RequestException:
            print(f"Encountered exception {e}")

    if api_type != "danbooru":
        # Attempt 'gelbooru' booru api setup [With support for JSON]
        try:
            package = format_package(tags, before_id, "gelbooru")
            result = session.get(api + "/index.php", params=package)
            if result.status_code == 200:
                data = result.json()
                if type(data) == list and type(data[0]) == dict:
                    api_type = "gelbooru"
            elif result.status_code == 403:
                scraper = cloudscraper.create_scraper()
                # result = scraper.get(api+'/index.php', params=package).text
                result = scraper.get(api + "/index.php", params=package)
                if result.status_code == 403:
                    print(f"No Dice. API endpoint for {api} is broken by cloudflare")
                elif result.status_code == 200:
                    data = result.json()
                    if type(data) == list and type(data[0]) == dict:
                        api_type = "gelbooru"
            else:
                raise requests.RequestException(
                    f"Error Status Code: {result.status_code}"
                )
        except Exception as e:
            if type(e) != requests.RequestException:
                print(f"Encountered exception {e}")

    print(f"Website {api} is of type {api_type}")
    return api_type


# TODO format_package will need to take booru_api and either: if not defined ('default') run backend code to
#  determine api endpoints
# TODO remove 'limit' flag for format_package as each booru is different and leaving blank should provide max
#  available for a given booru
def format_package(
    tags: typing.List[str],
    before_id: int,
    booru_api: str,
) -> typing.Dict[str, str]:
    """Formats package for session handler

    Package is a attribute used across the class to POST request data from
    the booru site, and this function provides the proper format for all
    other functions in the class that use ``self.package``.

    Args:
        tags (list): List of tags to search for.
        limit (int): Amount of posts to collect from the booru (Max of 320 for most websites)
        before_id (int): Last post ID to ignore (used to filter search to a certain page
            on the booru website)

    Warnings:
        ``tags`` attribute must be limited to 4 tags or less to properly be
        used in most booru websites
    """
    # Session package
    if booru_api == "danbooru":
        """Danbooru style sites have support for:

        ~ 4 tags with special tag formatting
        rating
        score

        special formatting for:
        page (b<post_id>)
        """
        package = {
            "page": f"b{before_id}",
            "tags": " ".join(tags),  # Reminder: hard limit of 4 tags
        }
    elif booru_api == "gelbooru":
        """
        Default requires the following:

        page is dapi (default booru api endpoint)
        s is post (search posts)
        q is index (show index of all posts)
        only one/two tags allowed - TODO determine if works
        """
        # Typical format for *most booru sites
        package = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "json": "1",
            "tags": " ".join(tags[:2]),  # 2 tags only for safety - truncates rating
        }
    else:
        package = {}
    return package
