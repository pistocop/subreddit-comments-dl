import sys
import csv
import json
import praw
import yaml
import typer
from datetime import datetime

# noinspection PyUnresolvedReferences
import pretty_errors  # keep the import to have better error messages

from os.path import join
from pathlib import Path
from typer import Argument
from typer import Option
from typing import Optional, List
from loguru import logger
from codetiming import Timer
from pushshift_py import PushshiftAPI
from prawcore.exceptions import NotFound


class OutputManager:
    """
    Class used to collect and store data (submissions and comments)
    """
    params_filename = "params.yaml"

    def __init__(self, output_dir: str, subreddit: str):
        self.submissions_list = []
        self.submissions_raw_list = []
        self.comments_list = []
        self.comments_raw_list = []
        self.run_id = datetime.today().strftime('%Y%m%d%H%M%S')

        self.subreddit_dir = join(output_dir, subreddit)
        self.runtime_dir = join(self.subreddit_dir, self.run_id)

        self.submissions_output = join(self.runtime_dir, "submissions")
        self.sub_raw_output = join(self.runtime_dir, "submissions", "raw")
        self.comments_output = join(self.runtime_dir, "comments")
        self.comments_raw_output = join(self.runtime_dir, "comments", "raw")
        self.params_path = join(self.runtime_dir, OutputManager.params_filename)

        self.total_submissions_counter = 0
        self.total_comments_counter = 0

        for path in [self.submissions_output,
                     self.sub_raw_output,
                     self.comments_output,
                     self.comments_raw_output]:
            Path(path).mkdir(parents=True, exist_ok=True)

    def reset_lists(self):
        self.submissions_list = []
        self.submissions_raw_list = []
        self.comments_list = []
        self.comments_raw_list = []

    def store(self, lap: str):
        # Track total data statistics
        self.total_submissions_counter += len(self.submissions_list)
        self.total_comments_counter += len(self.comments_list)

        # Store the collected data
        dictlist_to_csv(join(self.submissions_output, f"{lap}.csv"), self.submissions_list)
        dictlist_to_csv(join(self.comments_output, f"{lap}.csv"), self.comments_list)

        if len(self.submissions_raw_list) > 0:
            with open(join(self.sub_raw_output, f"{lap}.njson"), "a", encoding="utf-8") as f:
                f.write("\n".join(json.dumps(row) for row in self.submissions_raw_list))
        if len(self.comments_raw_list) > 0:
            with open(join(self.comments_raw_output, f"{lap}.njson"), "a", encoding="utf-8") as f:
                f.write("\n".join(json.dumps(row, default=lambda o: '<not serializable>')
                                  for row in self.comments_raw_list))

    def store_params(self, params: dict):
        with open(self.params_path, "w", encoding="utf-8") as f:
            yaml.dump(params, f)

    def load_params(self) -> dict:
        with open(self.params_path, "r", encoding="utf-8") as f:
            params = yaml.load(f, yaml.FullLoader)
        return params

    def enrich_and_store_params(self, utc_older: int, utc_newer: int):
        params = self.load_params()
        params["utc_older"] = utc_older
        params["utc_newer"] = utc_newer
        params["total_comments_counter"] = self.total_comments_counter
        params["total_submissions_counter"] = self.total_submissions_counter
        params["total_counter"] = self.total_comments_counter + self.total_submissions_counter
        self.store_params(params)


def dictlist_to_csv(file_path: str, dictionaries_list: List[dict]):
    if len(dictionaries_list) == 0:
        dictionaries_list = [{}]
    keys = dictionaries_list[0].keys()
    with open(file_path, 'w', newline='', encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, keys, dialect="excel")
        dict_writer.writeheader()
        dict_writer.writerows(dictionaries_list)


def init_locals(debug: str,
                output_dir: str,
                subreddit: str,
                utc_upper_bound: str,
                utc_lower_bound: str,
                run_args: dict,
                ) -> (str, OutputManager):
    assert not (utc_upper_bound and utc_lower_bound), "`utc_lower_bound` and " \
                                                      "`utc_upper_bound` parameters are in mutual exclusion"
    run_args.pop("reddit_secret")

    if not debug:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    direction = "after" if utc_upper_bound else "before"
    output_manager = OutputManager(output_dir, subreddit)

    output_manager.store_params(run_args)
    return direction, output_manager


def init_clients(reddit_id: str,
                 reddit_secret: str,
                 reddit_username: str
                 ) -> (PushshiftAPI, praw.Reddit):
    pushshift_api = PushshiftAPI()

    reddit_api = praw.Reddit(
        client_id=reddit_id,
        client_secret=reddit_secret,
        user_agent=f"python_script:subreddit_downloader:(by /u/{reddit_username})",
    )

    return pushshift_api, reddit_api


def utc_range_calculator(utc_received: int,
                         utc_upper_bound: int,
                         utc_lower_bound: int
                         ) -> (int, int):
    """
    Calculate the max UTC range seen.

    Increase/decrease utc_upper_bound/utc_lower_bound according with utc_received value
    """
    if not utc_upper_bound or not utc_lower_bound:
        utc_upper_bound = utc_received
        utc_lower_bound = utc_received

    utc_lower_bound = utc_lower_bound if utc_received > utc_lower_bound else utc_received
    utc_upper_bound = utc_upper_bound if utc_received < utc_upper_bound else utc_received

    return utc_lower_bound, utc_upper_bound


def comments_fetcher(sub, output_manager, reddit_api, comments_cap):
    """
    Comments fetcher
    Get all comments with depth-first approach
    Solution from https://praw.readthedocs.io/en/latest/tutorials/comments.html
    """
    try:
        submission_rich_data = reddit_api.submission(id=sub.id)
        logger.debug(f"Requesting {submission_rich_data.num_comments} comments...")
        submission_rich_data.comments.replace_more(limit=comments_cap)
        comments = submission_rich_data.comments.list()
    except NotFound:
        logger.warning(f"Submission not found in PRAW: `{sub.id}` - `{sub.title}` - `{sub.full_link}`")
        return
    for comment in comments:
        comment_useful_data = {
            "id": comment.id,
            "submission_id": sub.id,
            "body": comment.body.replace('\n', '\\n'),
            "created_utc": int(comment.created_utc),
            "parent_id": comment.parent_id,
            "permalink": comment.permalink,
        }
        output_manager.comments_raw_list.append(comment.__dict__)
        output_manager.comments_list.append(comment_useful_data)


def submission_fetcher(sub, output_manager: OutputManager):
    """
    Get and store reddit submission info
    """
    # Sometimes the submission doesn't have the selftext
    self_text_normalized = sub.selftext.replace('\n', '\\n') if hasattr(sub, "selftext") else "<not selftext available>"

    submission_useful_data = {
        "id": sub.id,
        "created_utc": sub.created_utc,
        "title": sub.title.replace('\n', '\\n'),
        "selftext": self_text_normalized,
        "full_link": sub.full_link,
    }
    output_manager.submissions_list.append(submission_useful_data)
    output_manager.submissions_raw_list.append(sub.d_)


class HelpMessages:
    help_reddit_url = "https://github.com/reddit-archive/reddit/wiki/OAuth2"
    help_reddit_agent_url = "https://github.com/reddit-archive/reddit/wiki/API"
    help_praw_replace_more_url = "https://asyncpraw.readthedocs.io/en/latest/code_overview/other/commentforest.html#asyncpraw.models.comment_forest.CommentForest.replace_more"

    subreddit = "The subreddit name"
    output_dir = "Optional output directory"
    batch_size = "Request `batch_size` submission per time"
    laps = "How many times request `batch_size` reddit submissions"
    reddit_id = f"Reddit client_id, visit {help_reddit_url}"
    reddit_secret = f"Reddit client_secret, visit {help_reddit_url}"
    reddit_username = f"Reddit username, used for build the `user_agent` string, visit {help_reddit_agent_url}"
    utc_after = "Fetch the submissions after this UTC date"
    utc_before = "Fetch the submissions before this UTC date"
    debug = "Enable debug logging"
    comments_cap = f"Some submissions have 10k> nested comments and stuck the praw API call." \
                   f"If provided, the system requires new comments `comments_cap` times to the praw API." \
                   f"`comments_cap` under the hood will be passed directly to `replace_more` function as " \
                   f"`limit` parameter. For more info see the README and visit {help_praw_replace_more_url}."


# noinspection PyTypeChecker
@Timer(name="main", text="Total downloading time: {minutes:.1f}m", logger=logger.info)
def main(subreddit: str = Argument(..., help=HelpMessages.subreddit),
         output_dir: str = Option("./data/", help=HelpMessages.output_dir),
         batch_size: int = Option(10, help=HelpMessages.batch_size),
         laps: int = Option(3, help=HelpMessages.laps),
         reddit_id: str = Option(..., help=HelpMessages.reddit_id),
         reddit_secret: str = Option(..., help=HelpMessages.reddit_secret),
         reddit_username: str = Option(..., help=HelpMessages.reddit_username),
         utc_after: Optional[str] = Option(None, help=HelpMessages.utc_before),
         utc_before: Optional[str] = Option(None, help=HelpMessages.utc_before),
         comments_cap: Optional[int] = Option(None, help=HelpMessages.comments_cap),
         debug: bool = Option(False, help=HelpMessages.debug),
         ):
    """
    Download all the submissions and relative comments from a subreddit.
    """

    # Init
    utc_upper_bound = utc_after
    utc_lower_bound = utc_before
    direction, out_manager = init_locals(debug,
                                         output_dir,
                                         subreddit,
                                         utc_upper_bound,
                                         utc_lower_bound,
                                         run_args=locals())
    pushshift_api, reddit_api = init_clients(reddit_id, reddit_secret, reddit_username)
    logger.info(f"Start download: "
                f"UTC range: [{utc_lower_bound}, {utc_upper_bound}], "
                f"direction: `{direction}`, "
                f"batch size: {batch_size}, "
                f"total submissions to fetch: {batch_size * laps}")

    # Start the gathering
    for lap in range(laps):
        logger.debug(f"New lap start: {lap}")
        lap_message = f"Lap {lap}/{laps} completed in ""{minutes:.1f}m | " \
                      f"[new/tot]: {len(out_manager.comments_list)}/{out_manager.total_comments_counter}"

        with Timer(text=lap_message, logger=logger.info):
            # Reset the data already stored
            out_manager.reset_lists()

            # Fetch data in the `direction` way
            submissions_generator = pushshift_api.search_submissions(subreddit=subreddit,
                                                                     limit=batch_size,
                                                                     sort='desc' if direction == "before" else 'asc',
                                                                     sort_type='created_utc',
                                                                     after=utc_upper_bound if direction == "after" else None,
                                                                     before=utc_lower_bound if direction == "before" else None,
                                                                     )

            for sub in submissions_generator:
                logger.debug(f"New submission `{sub.full_link}` - created_utc: {sub.created_utc}")

                # Fetch the submission data
                submission_fetcher(sub, out_manager)

                # Fetch the submission's comments
                comments_fetcher(sub, out_manager, reddit_api, comments_cap)

                # Calculate the UTC seen range
                utc_lower_bound, utc_upper_bound = utc_range_calculator(sub.created_utc,
                                                                        utc_upper_bound,
                                                                        utc_lower_bound)
            # Store data (submission and comments)
            out_manager.store(lap)

            # Check the bounds
            assert utc_lower_bound < utc_upper_bound, f"utc_lower_bound '{utc_lower_bound}' should be " \
                                                      f"less than utc_upper_bound '{utc_upper_bound}'"
        logger.debug(f"utc_upper_bound: {utc_upper_bound} , utc_lower_bound: {utc_lower_bound}")

    out_manager.enrich_and_store_params(utc_newer=utc_upper_bound, utc_older=utc_lower_bound)
    logger.info(f"Stop download: lap {laps}/{laps} [total]: {out_manager.total_comments_counter}")


if __name__ == '__main__':
    typer.run(main)
