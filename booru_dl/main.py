"""Downloader for the booru-dl program

Contains the main class ``Downloader()`` that is used to:
    * Collect configuration data
    * Search Sections from the config
    * Download files from the config

To perform these functions, ``Downloader()`` uses the ``config.Section()`` and ``config.Config()``
classes from ``library/config.py`` and collects session data from ``library/backend.py``

Please see :doc:`config` and :doc:`backend` for more details on how these library files are used.
"""
# mypy: ignore-errors
import logging
import os
import pathlib
import time
from datetime import datetime
from time import sleep

import requests

from booru_dl.library import backend
from booru_dl.library import config as cfg
from booru_dl.library.backend import format_package


class Downloader:
    """Download class for the Booru using a given config file

    Args:
        config_loc (str): Default of ``config.ini``, any config file provided

    Warnings:
        ``config_loc`` must be of type ``str`` and not contain anything other than the file name.
        The file should be located in same directory as this python file.
    """

    def __init__(
        self,
        config_loc: str = "config.ini",
    ):  # Self-starting function
        logging.info("Starting Booru downloader [v1.0.0]")

        self.path = pathlib.PurePath(".")
        self.filepath = self.path.joinpath("downloads")
        logging.debug(f"Root path: {os.path.abspath(self.path)}")
        logging.debug(f"Downloads folder path: {os.path.abspath(self.filepath)}")

        # Makes all needed directories
        os.makedirs(self.filepath, exist_ok=True)

        # Collects config and Session
        self.config = cfg.Config(config_loc)
        # TODO extract session to run on post basis (likely)
        self.session = backend.get_session(self.config.useragent)  # Get useragent

        # Collects metadata
        # TODO add support for multiple uri, api_keys, and usernames - will be implemented in config
        self.URI = self.config.uri
        # self.API = self.config.api
        # self.USER = self.config.user
        # TODO add support for multiple blacklists PER URI (possible but is it needed?)
        self.blacklist = self.config.blacklist

    # TODO refactor get_data to be more modular in format
    def get_data(self):
        """Collects all data from the sections determined on class instantiation

        For each section to download, takes the criteria provided and POST requests
        the booru site provided until a flag is reached (eg. Past days allowed, end of
        provided input from booru site)
        """
        func_result = 0
        start = time.time()
        for section_name in self.config.posts:
            logging.info(f'Beginning Download of section "{section_name}"')
            section: cfg.Section = self.config.posts[section_name]
            # 3 tags + score + rating for filtering
            # TODO package must be changed per-api endpoint - will need nested loop to run <Section> per <URI>
            # TODO also update format_package to support multiple API endpoints (via backend class)
            #  for best result, will likely need to refactor this into backend OR update get_posts to run format_package
            for api in section.api_endpoint:
                booru_type = self.config.uri[api][2]
                if booru_type != "None":
                    logging.info(f"Beginning collection from '{api}' [{section_name}]")
                    before_id = 10000000
                    if len(section.rating) > 1:
                        self.package = format_package(
                            section.tags[:3] + [f"score:>={section.min_score}"],
                            before_id,
                            booru_api=booru_type,  # List contains booru type at index 2
                        )
                    else:
                        self.package = format_package(
                            section.tags[:4]
                            + [
                                f"score:>={section.min_score}",
                                f"rating:{section.rating[0]}",
                            ],
                            before_id,
                            booru_api=booru_type,
                        )
                    # Check for file collection issues
                    if not func_result:
                        func_result = self.get_posts(section, api, booru_type)
                        if func_result == 1:
                            logging.error(
                                f"Problem with post collection for api {api} - Too High post requirements likely"
                            )
                    else:
                        self.get_posts(section, api, booru_type)
                else:
                    logging.error(
                        f"Detected broken API {api} - Remove from config or send info to developer if bug"
                    )
                    func_result = 1

        logging.info(
            f"All Sections have been collected (Total execution time of {time.time() - start:.2f}s)"
        )
        return func_result  # if any post collection failed should return 1

    # TODO: refactor this into backend and/or combine with already available backend.request_uri()
    # TODO: remove session from required variables as it is a global class variable
    def download_file(
        self, session: requests.Session, url: str, section: str, file_name: str
    ):
        """Downloads the given file url to a provided Section folder

        Args:
            session (requests.Session): A user-agent created by the backend script for web handling
            url (str): URL/URI of the exact location of the file to download
            section (str): Section Name to place file within (Can be a path-like string eg. ``'foo/bar'``)
            file_name (str): Name to be used for the file

        Returns:
            (int): 0 if successful, or -1 if a problem occurs
        """
        # TODO optional file sorting
        file_name = (
            file_name + "." + (url.split("/")[-1].split(".")[-1])
        )  # makes file_name 'file_name.<extension>'

        filepath = self.filepath.joinpath(pathlib.PurePath(section + "/"))
        if os.path.exists(
            filepath.joinpath(file_name)
        ):  # no point in downloading what we already have
            logging.debug(f"File {file_name} already exists - Skipping")
            return 1
        else:
            os.makedirs(filepath, exist_ok=True)
        # TODO api broken atm
        # if self.USER and self.API:
        #     result = session.get(url, stream=True, auth=(self.USER, self.API))
        # else:
        result = session.get(url, stream=True)
        if result.status_code == 200:
            with open(filepath.joinpath(file_name), "wb") as f:
                for chunk in result.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logging.debug(f"Downloaded {file_name} to {filepath.joinpath(file_name)}")
            return file_name
        else:
            logging.error(
                f"Error downloading {file_name} [Status Code: {result.status_code}]"
            )
            # DEBUG to file
            return -1

    # TODO: tags are not yet checked for boorus - eventually add support once api support is done
    # TODO: update variables used in the function to take global class variables where available

    def get_posts(self, section: cfg.Section, url: str, endpoint: str):
        """Collects all posts given a certain config section and its respective metadata

        Note:
            The section attribute contains many fields required for determination of which post(s)
            to collect for a given Section, please see documentation of the Section class within :doc:`config`

        Args:
            section (cfg.Section): Section class containing all metadata for the requested section
        """
        # TODO check tag validity

        # Sections stuff
        max_time = section.days * 86400  # seconds
        min_faves = section.min_faves
        min_score = section.min_score

        package = self.package

        # 'Telemetry'
        start = datetime.now().timestamp()
        last_id = 100000000  # arbitrarily big number
        total_posts = 0
        searched_posts = 0
        skipped_files = 0
        loop = 1  # loop tracking

        # Main function loop
        while last_id > 1:
            # TODO api needs to be fixed
            # if self.USER and self.API:
            #     current_batch = backend.request_uri(
            #         self.session,
            #         self.config.paths[url]["POST_URI"],
            #         package,
            #         (self.USER, self.API),
            #     )
            #     current_batch = current_batch.json()["posts"]
            #
            # else:
            current_batch = backend.request_uri(
                self.session, self.config.paths[url]["POST_URI"], package
            ).json()
            if len(current_batch) > 0:
                if type(current_batch) == dict:
                    current_batch = current_batch["posts"]
            else:
                logging.warning(
                    f"No Data for API {url} - Perhaps the requirements are too high"
                )
                return 1

            for post in current_batch:
                searched_posts += 1
                # Simple profiling setup
                post_start = time.time()

                # Attempt collection of post attributes - skip post if issues
                try:
                    last_id = post_id = self.collect_post_id(post)
                    file_ext, file = self.collect_post_file(post, post_id)
                    tags = self.collect_post_tags(post, post_id)
                except AssertionError:
                    continue

                if file_ext not in section.allowed_types:
                    logging.debug(
                        f"Post {post_id} was skipped due to being extension "
                        f"[{file_ext}] (Not in allowed extensions)"
                    )
                    continue

                # Collect post score
                score = 0
                if "score" in post and type(post["score"]) == int:
                    score = post["score"]
                elif "score" in post and type(post["score"]) == dict:
                    score = post["score"]["total"]

                faves = post["fav_count"] if "fav_count" in post else 0
                rating = post["rating"]

                # TODO refactor time to separate function to support multiple APIs
                try:
                    post_time = datetime.fromisoformat(post["created_at"]).timestamp()
                except ValueError:
                    post_time = time.mktime(
                        time.strptime(post["created_at"], "%a %b %d %H:%M:%S %z %Y")
                    )

                    # TODO refactor all checks to separate function - also re-add min_score test
                # Check for invalid files
                if start - post_time > max_time:  # invalid time
                    # print(f'Debug: Too low time {post_id}')
                    last_id = 0
                    break
                if rating not in section.rating:
                    # print(f'Debug: Rating wrong {post_id}')
                    continue
                if faves < min_faves:  # invalid favcount
                    logging.debug(
                        f"Post {post_id} has {faves} favorites "
                        f"(Lower than criteria of {min_faves}) - Skipping file"
                    )
                    continue

                if score < min_score:  # invalid score
                    logging.debug(
                        f"Post {post_id} has {score} score "
                        f"(Lower than criteria of {min_score}) - Skipping file"
                    )
                    continue
                # Check if any blacklisted tags exist, and if so skip
                blacklisted = False
                for tag in tags:  # invalid tags
                    if tag in self.blacklist:
                        # A tag can be blacklist-ignored per section
                        # but will iterate through all tags to ensure there aren't any actual blacklisted ones
                        if len(section.ignore_tags) > 0 and tag in section.ignore_tags:
                            logging.debug(
                                f'Ignored blacklisted tag "{tag}" for post {post_id}, '
                                f'due to section "{section.name}" settings'
                            )
                        else:
                            logging.debug(
                                f'Found blacklisted tag "{tag}" for post {post_id} - Skipping file'
                            )
                            blacklisted = True
                            break  # skip file
                if blacklisted:
                    continue

                # TODO refactor this to use the function to obtain file url for multi endpoints
                # Download the file if not blacklisted and stuff
                file_name = self.download_file(
                    self.session, file, f"{section.name}/{url}", str(post_id)
                )  # 3rd argument is file name (optional)
                if file_name == 1:
                    skipped_files += 1
                    continue

                # TODO add support for determination of status code errors related to
                #  too many requests and update timing based on error
                # Check timing and ensure 2 requests a second compliance
                post_finish = time.time()
                post_timing = post_finish - post_start
                if post_timing < 0.5:
                    # print(f'sleeping for a little more ({0.5-post_timing})') - removed due to how many times it occurs
                    sleep(0.5 - post_timing)

                total_posts += 1  # If reach here post was acquired

            # TODO Add info on which URI is being searched - add support for multiple api searches simultaneously
            #  this will require multiprocessing and refactor of code body of function to a parameterized function
            if searched_posts > 0 and len(current_batch) > 0:
                logging.info(
                    f"API Search {loop} - {total_posts} Downloaded / {skipped_files} Already Downloaded "
                    f"({100 * ((total_posts + skipped_files) / searched_posts):.2f}% posts collected from search)]"
                )
            # If less than 10% of files are touched after 5 or more loops (wasted effort)
            if (
                searched_posts > 0
                and (100 * ((total_posts + skipped_files) / searched_posts)) < 10
                and loop >= 5
            ):
                logging.error(
                    f"Limited posts were downloaded after {loop} search loops - "
                    f"Please ensure your configuration is reasonable to prevent wasted searches"
                )
                break
            logging.debug(
                f"{total_posts + skipped_files} Files collected (or cached); {searched_posts} Searched"
            )
            if last_id == 0:
                logging.info(
                    f"Downloaded all valid posts for the given days ({section.days})"
                )
                break
            # Reached end of possible images to download
            if (
                len(current_batch) < 20
            ):  # assume minimum size of 20 - TODO per-api check of return amount
                break
            else:
                loop += 1
                package["page"] = f"b{last_id}"
        end = time.time()
        logging.info(
            f'All done! Execution took {end - start:.2f} seconds for "{section.name}" [API {url}]'
        )
        return 0

    def collect_key(self, expected_types: list, post: dict, id=None):
        """Collect post keys based on expected types

        This helper function determines what key is found and then passes resulting data and key type to
        the function that called it.

        Args:
            expected_types (list of string): Keys expected to be found in the API result
            post (dict): The full JSON-typed post data used to collect data from

        Returns:
            str: Successful API key found for metadata

        Raises:
            KeyError: if keys don't exist at all - provides full dictionary back to help in debugging
        """
        result_key = [
            key for key in expected_types for posts in post.keys() if key == posts
        ]
        if len(result_key) > 1:
            if id:
                logging.warning(
                    f"Multiple valid keys found - Something is wrong with post {id}"
                )
                logging.warning(f"Valid keys were: {result_key}")
            else:
                logging.warning(
                    f"Multiple valid keys found - Something is wrong with post {post[result_key[0]]}"
                )
                logging.warning(f"Valid keys were: {result_key}")
            return result_key[0]
        elif result_key:
            return result_key[0]
        else:
            raise KeyError(f"No Expected keys found for {post}")

    def collect_post_id(self, post: dict):
        """Collect post ID from a given JSON-typed post

        Args:
            post (dict): Post to perform analysis on

        Returns:
            int: Post ID

        Raises:
            ValueError: Unknown ID type for post [Missing keys]
            AssertionError: ``ID`` variable was not properly set to int-type or not found
        """
        # keys = ["id"] Key will only be ID (as far as I know*)
        id = 0
        try:
            if type(post["id"]) == str:
                id = int(post["id"])
            elif type(post["id"]) == int:
                id = post["id"]
            else:
                raise ValueError(
                    f'Unknown type for ID {post["id"]} [{type(post["id"])}]'
                )
        except KeyError as e:
            logging.debug(e)  # Key issue
            logging.error("Cannot find post ID for API file - Possibly hidden file")
            raise e
        except ValueError as e:
            logging.error(e)  # Value issue
            raise e
        assert type(id) == int and id > 0
        return id

    def collect_post_tags(self, post: dict, id: int):
        """Collect post tags from a given JSON-typed post

        Args:
            post (dict): Post to perform analysis on

        Returns:
            list: List of strings of tags for the post

        Raises:
            ValueError: Unknown tag type for post [Missing keys]
            AssertionError: ``Tag`` variable was not properly set to a list of strings
        """
        keys = ["tags", "tag_string"]
        tags = None
        try:
            result = self.collect_key(keys, post, id)
            if result == "tags":
                if type(post["tags"]) == str:
                    tags = post["tags"].split()
                elif type(post["tags"]) == dict:
                    tags = (
                        (category := post["tags"])["general"]
                        + category["species"]
                        + category["character"]
                        + category["copyright"]
                        + category["artist"]
                        + category["invalid"]
                        + category["lore"]
                        + category["meta"]
                    )
                else:
                    raise ValueError(
                        f'Unknown type for tags {post["tags"]} [{type(post["tags"])}]'
                    )
            elif result == "tag_string":
                tags = post["tag_string"].split()

        except KeyError as e:
            logging.error(e)  # Key issue
            raise e
        except ValueError as e:
            logging.error(e)  # Value issue
            raise e
        assert type(tags) == list
        return tags

    def collect_post_file(self, post: dict, id: int):
        """Collect post file from a given JSON-typed post

        Args:
            post (dict): Post to perform analysis on
            id (int): ID of given post for logging of issues

        Returns:
            tuple of str: File extension and File URL

        Raises:
            ValueError: Unknown file_url type for post [Missing keys]
            AssertionError: ``file_ext`` and ``file`` variable were not properly set to strings
        """
        keys = ["file_url", "file"]
        file = None
        file_ext = None
        try:
            result = self.collect_key(keys, post)
            if result == "file_url":
                if type(post["file_url"]) == str:
                    file_ext = post["file_url"].split("/")[-1].split(".")[-1]
                    file = post["file_url"]
                else:
                    raise ValueError(
                        f'Unknown type for file_url {post["file_url"]} [{type(post["file_url"])}]'
                    )
            elif result == "file" and "url" in post["file"]:
                if post["file"]["url"]:
                    file_ext = post["file"]["url"].split("/")[-1].split(".")[-1]
                    file = post["file"]["url"]
                else:
                    logging.warning(
                        f"File access for Post {id} blocked by site - possibly requires API access"
                    )
            else:
                raise ValueError("Unknown type for file - No Data")
        except KeyError as e:
            logging.error(e)  # Key issue
            raise e
        except ValueError as e:
            logging.error(e)  # Value issue
            raise e
        assert type(file) == str and type(file_ext) == str
        return file_ext, file


if __name__ == "__main__":
    logger = backend.set_logger(logging.getLogger(), "booru-dl.log")
    # Main entrypoint
    downloader = Downloader()
    downloader.get_data()
    os.system("pause")  # Warn: Windows only
