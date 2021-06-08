"""
Main entrypoint of program. Docs TBD.
"""
import logging
import os
import time
import typing
from datetime import datetime
from time import sleep

from library import backend
from library import config as cfg
from library import constants

logger = logging.getLogger(__file__)


class Downloader:
    session = backend.get_session()  # Get useragent
    filepath = "downloads"  # Default
    blacklist: typing.List[str] = []
    package: typing.Dict[str, object] = {}

    def __init__(self, config_loc: str = "config.ini"):  # Self-starting function
        os.makedirs(self.filepath, exist_ok=True)
        logger.info("Starting Booru downloader [v1.0.0]")
        self.URI = constants.main()
        self.config = cfg.Config(config_loc)
        self.blacklist = self.config.blacklist

        for section in self.config.posts:
            logger.info(f'Beginning Download of section "{section}"')
            sct: cfg.Section = self.config.posts[section]
            # 3 tags + score + rating for filtering
            self.format_package(
                sct.tags[:3] + [f"score:>={sct.min_score}", f"rating:{sct.rating}"]
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

        if os.path.exists(
            self.filepath + "\\" + section + "\\" + file_name
        ):  # no point in downloading what we already have
            # DEBUG
            logger.debug(f"File {file_name} already exists - Skipping")
            return 1
        else:
            os.makedirs(self.filepath + "\\" + section, exist_ok=True)
        result = session.get(url, stream=True)
        if result.status_code == 200:
            path = self.filepath + "\\" + section + "\\" + file_name
            with open(path, "wb") as f:
                for chunk in result.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
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
        min_favs = section.min_favs

        package = self.package
        # TODO allowed ... = config.extensions
        allowed_extensions = ["jpg", "gif", "png"]  # TODO optional

        # 'Telemetry'
        start = datetime.now().timestamp()
        last_id = 100000000  # arbitrarily big number
        total_posts = 0
        max_limit = package["limit"]
        loop = 1  # loop tracking
        print(
            "No Debug/Info is provided per loop at the moment unless required"
        )  # TODO :P

        # Main function loop
        while last_id > 1:
            logger.info(
                f"Current ({max_limit} Posts) Loop: {loop} - Total Posts Downloaded: {total_posts}"
            )
            current_batch = backend.request_uri(
                self.session, self.URI["POST_URI"], package
            ).json()["posts"]
            for post in current_batch:
                # Simple profiling setup
                post_start = time.time()

                # Check for bad extensions
                file_ext = post["file"]["url"].split("/")[-1].split(".")[-1]
                if file_ext not in allowed_extensions:
                    # print(post['id'],file_ext)
                    continue

                # Metadata - TODO re-enable typed tags
                post_id = post["id"]
                tags = (
                    (category := post["tags"])["general"]
                    + category["species"]
                    + category["copyright"]
                )
                score = post["score"]["total"]
                favs = post["fav_count"]
                rating = post["rating"]
                post_time = datetime.fromisoformat(post["created_at"]).timestamp()

                # Check for invalid files
                if rating not in section.rating:
                    # print(f'Debug: Rating wrong {post_id}')
                    continue
                if start - post_time > max_time:  # invalid time
                    # print(f'Debug: Too low time {post_id}')
                    logger.info(
                        f"Downloaded all valid posts for the given days ({section.days})"
                    )
                    last_id = 0
                    break
                if score < min_score:  # invalid score
                    # TODO debugstatement
                    # print(f'Debug: Too low score {post_id}')
                    continue
                if favs < min_favs:  # invalid favcount
                    # print(f'Debug: Too low favcount {post_id}')
                    # TODO debugstatement
                    continue
                for tag in tags:  # invalid tags
                    if tag in self.blacklist:
                        # TODO debugstatement
                        continue  # skip file

                # Download the file if not blacklisted and stuff
                file_name = self.download_file(
                    self.session, post["file"]["url"], section.name, str(post_id)
                )  # 3rd argument is file name (optional)
                if file_name == 1:
                    continue

                last_id = int(post_id)

                # Check timing and ensure 2 requests a second compliance
                post_finish = time.time()
                post_timing = post_finish - post_start
                if post_timing < 0.5:
                    # print(f'sleeping for a little more ({0.5-post_timing})') - removed due to how many times it occurs
                    sleep(0.5 - post_timing)

                total_posts += 1  # If reach here post was acquired

            # Reached end of possible images to download
            if len(current_batch) < 300:
                break
            else:
                loop += 1
                package["page"] = f"b{last_id}"
        end = time.time()
        logger.info(f"All done! Execution took {end-start:.2f} seconds")


if __name__ == "__main__":
    logger = backend.set_logger(logger, "booru-dl.log")
    # Main entrypoint
    Downloader()
