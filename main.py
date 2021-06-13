"""
Main entrypoint of program. Docs TBD.
"""
import logging
import os
import pathlib
import time
import typing
from datetime import datetime
from time import sleep

from library import backend
from library import config as cfg

logger = logging.getLogger(__file__)


class Downloader:
    blacklist: typing.List[str] = []
    package: typing.Dict[str, object] = {}

    path = os.path.dirname(__file__)
    filepath = pathlib.PurePath(path + "/downloads")

    def __init__(
        self, config_loc: str = "config.ini", run: bool = True
    ):  # Self-starting function
        os.makedirs(self.filepath, exist_ok=True)
        logger.info("Starting Booru downloader [v1.0.0]")
        self.config = cfg.Config(config_loc)
        self.session = backend.get_session(self.config.useragent)  # Get useragent

        self.URI = self.config.uri
        self.API = self.config.api
        self.USER = self.config.user

        self.blacklist = self.config.blacklist
        if run:
            self.get_data()

    def get_data(self):
        for section in self.config.posts:
            logger.info(f'Beginning Download of section "{section}"')
            sct: cfg.Section = self.config.posts[section]
            # 3 tags + score + rating for filtering
            if len(sct.rating) > 1:
                self.format_package(sct.tags[:3] + [f"score:>={sct.min_score}"])
            else:
                self.format_package(
                    sct.tags[:4]
                    + [f"score:>={sct.min_score}", f"rating:{sct.rating[0]}"]
                )
            # DEBUG print(self.package)
            self.get_posts(sct)

    def format_package(self, tags, limit: int = 320, before_id: int = 100000000):
        """Formats package for session handler"""
        # Session package
        package = {
            "page": f"b{before_id}",
            "limit": limit,  # Reminder: max limit of 320
            "tags": " ".join(tags),  # Reminder: hard limit of 4 tags
        }

        self.package = package

    def download_file(self, session, url, section, file_name):
        """Downloads the given file"""
        # TODO optional file sorting
        file_name = (
            file_name + "." + (url.split("/")[-1].split(".")[-1])
        )  # makes file_name 'file_name.<extension>'

        filepath = self.filepath.joinpath(pathlib.PurePath(section + "/"))
        if os.path.exists(
            filepath.joinpath(file_name)
        ):  # no point in downloading what we already have
            logger.debug(f"File {file_name} already exists - Skipping")
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
            logger.debug(f"Downloaded {file_name} to {filepath.joinpath(file_name)}")
            return file_name
        else:
            logger.error(
                f"Error downloading {file_name} [Status Code: {result.status_code}]"
            )
            # DEBUG to file
            return -1

    def get_posts(self, section):
        """Collects all posts given a certail config section and its respective metadata"""
        # TODO check tag validity

        # Sections stuff
        max_time = section.days * 86400  # seconds
        min_score = section.min_score
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
                current_batch = (
                    current_batch.json()["posts"] if type(current_batch) != int else []
                )
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
                    logger.warning(
                        f"File access for Post #{post_id} blocked by site - possibly requires API access"
                    )
                    continue
                if file_ext not in section.allowed_types:
                    logger.debug(
                        f"Post #{post_id} was skipped due to being extension "
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
                score = post["score"]["total"]
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
                if score < min_score:  # invalid score
                    logger.debug(
                        f"Post {post_id} has {score} score "
                        f"(Lower than criteria of {min_score}) - Skipping file"
                    )
                    continue
                if faves < min_faves:  # invalid favcount
                    logger.debug(
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
                        if tag in section.ignore_tags:
                            logger.debug(
                                f'Found blacklisted tag "{tag}" for post {post_id}, '
                                f"However found tag in ignore_tags for section {section.name}"
                            )
                        else:
                            logger.debug(
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

            logger.info(
                f"API Search {loop} - {total_posts} Downloaded / {skipped_files} Already Downloaded "
                f"({100 * ((total_posts + skipped_files) / searched_posts):.2f}% posts collected from search)]"
            )
            if last_id == 0:
                logger.info(
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
        logger.info(
            f'All done! Execution took {end - start:.2f} seconds for "{section.name}"'
        )


if __name__ == "__main__":
    logger = backend.set_logger(logger, "booru-dl.log")
    # Main entrypoint
    Downloader()
