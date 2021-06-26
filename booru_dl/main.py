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
import typing
from datetime import datetime
from time import sleep

import requests

from booru_dl.library import backend
from booru_dl.library import config as cfg


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
        self.URI = self.config.uri
        self.API = self.config.api
        self.USER = self.config.user
        self.blacklist = self.config.blacklist

    def get_data(self):
        """Collects all data from the sections determined on class instantiation

        For each section to download, takes the criteria provided and POST requests
        the booru site provided until a flag is reached (eg. Past days allowed, end of
        provided input from booru site)
        """
        start = time.time()
        for section_name in self.config.posts:
            logging.info(f'Beginning Download of section "{section_name}"')
            section: cfg.Section = self.config.posts[section_name]
            # 3 tags + score + rating for filtering
            if len(section.rating) > 1:
                self.format_package(section.tags[:3] + [f"score:>={section.min_score}"])
            else:
                self.format_package(
                    section.tags[:4]
                    + [f"score:>={section.min_score}", f"rating:{section.rating[0]}"]
                )
            # DEBUG print(self.package)
            self.get_posts(section)
        logging.info(
            f"All Sections have been collected (Total execution time of {time.time() - start:.2f}s)"
        )

    def format_package(
        self, tags: typing.List[str], limit: int = 320, before_id: int = 100000000
    ):
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
        package = {
            "page": f"b{before_id}",
            "limit": limit,  # Reminder: max limit of 320
            "tags": " ".join(tags),  # Reminder: hard limit of 4 tags
        }

        self.package = package

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
        if self.USER and self.API:
            result = session.get(url, stream=True, auth=(self.USER, self.API))
        else:
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

    def get_posts(self, section: cfg.Section):
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

            if self.USER and self.API:
                current_batch = backend.request_uri(
                    self.session,
                    self.config.paths["POST_URI"],
                    package,
                    (self.USER, self.API),
                )
                current_batch = current_batch.json()["posts"]

            else:
                current_batch = backend.request_uri(
                    self.session, self.config.paths["POST_URI"], package
                ).json()["posts"]

            for post in current_batch:
                searched_posts += 1
                # Simple profiling setup
                post_start = time.time()
                last_id = int(
                    (post_id := post["id"])
                )  # Set the new last_id to the last available post ran
                # Check for bad extensions
                if post["file"]["url"]:
                    file_ext = post["file"]["url"].split("/")[-1].split(".")[-1]
                else:
                    logging.warning(
                        f"File access for Post {post_id} blocked by site - possibly requires API access"
                    )
                    continue
                if file_ext not in section.allowed_types:
                    logging.debug(
                        f"Post {post_id} was skipped due to being extension "
                        f"[{file_ext}] (Not in allowed extensions)"
                    )
                    continue

                # Metadata - TODO re-enable typed tags
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
                # score = post["score"]["total"] #TODO unused but could be useful
                faves = post["fav_count"]
                rating = post["rating"]
                post_time = datetime.fromisoformat(post["created_at"]).timestamp()

                # Check for invalid files
                if rating not in section.rating:
                    # print(f'Debug: Rating wrong {post_id}')
                    continue
                if start - post_time > max_time:  # invalid time
                    # print(f'Debug: Too low time {post_id}')
                    last_id = 0
                    break
                if faves < min_faves:  # invalid favcount
                    logging.debug(
                        f"Post {post_id} has {faves} favorites "
                        f"(Lower than criteria of {min_faves}) - Skipping file"
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

                # Download the file if not blacklisted and stuff
                file_name = self.download_file(
                    self.session, post["file"]["url"], section.name, str(post_id)
                )  # 3rd argument is file name (optional)
                if file_name == 1:
                    skipped_files += 1
                    continue

                # Check timing and ensure 2 requests a second compliance
                post_finish = time.time()
                post_timing = post_finish - post_start
                if post_timing < 0.5:
                    # print(f'sleeping for a little more ({0.5-post_timing})') - removed due to how many times it occurs
                    sleep(0.5 - post_timing)

                total_posts += 1  # If reach here post was acquired

            logging.info(
                f"API Search {loop} - {total_posts} Downloaded / {skipped_files} Already Downloaded "
                f"({100 * ((total_posts + skipped_files) / searched_posts):.2f}% posts collected from search)]"
            )
            logging.debug(
                f"{total_posts + skipped_files} Files collected (or cached); {searched_posts} Searched"
            )
            if last_id == 0:
                logging.info(
                    f"Downloaded all valid posts for the given days ({section.days})"
                )
                break
            # Reached end of possible images to download
            if len(current_batch) < 300:
                break
            else:
                loop += 1
                package["page"] = f"b{last_id}"
        end = time.time()
        logging.info(
            f'All done! Execution took {end - start:.2f} seconds for "{section.name}"'
        )


if __name__ == "__main__":
    logger = backend.set_logger(logging.getLogger(), "booru-dl.log")
    # Main entrypoint
    downloader = Downloader()
    downloader.get_data()
    os.system("pause")  # Warn: Windows only
