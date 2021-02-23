# subreddit-comments-dl

<a href="https://gitmoji.carloscuesta.me">
  <img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=flat-square" alt="Gitmoji">
</a>

> Download all the text comments from a subreddit


Use the
script [subreddit_downloader.py](https://github.com/pistocop/subreddit-comments-dl/blob/master/src/subreddit_downloader.py)
multiple times to download the data.<br>
Then run the
script [dataset_builder.py](https://github.com/pistocop/subreddit-comments-dl/blob/master/src/dataset_builder.py) for
create a unique dataset.

🖱 More info on [website](https://www.pistocop.dev/posts/subreddit_downloader/).

## :rocket: Usage

Basic usage to download submissions and relative comments from
subreddit [AskReddit](https://www.reddit.com/r/AskReddit/) and [News](https://www.reddit.com/r/news/):

```shell
# Install the dependencies
pip install -r requirements.txt

# Download the AskReddit comments of the last 30 submissions
python src/subreddit_downloader.py AskReddit --batch-size 10 --laps 3 --reddit-id <reddit_id> --reddit-secret <reddit_secret> --reddit-username <reddit_username>

# Download the News comments after 1 January 2020
python src/subreddit_downloader.py News --batch-size 512 --laps 3 --reddit-id <reddit_id> --reddit-secret <reddit_secret> --reddit-username <reddit_username> --utc-after 1609459201

# Build the dataset, the results will be under `./dataset/` path
python src/dataset_builder.py 
```

### :information_source: Where I can get the reddit parameters?

- Parameters indicated with `<...>` on the previous script
- Official [Reddit guide](https://github.com/reddit-archive/reddit/wiki/OAuth2)
- TLDR: read this [stack overflow](https://stackoverflow.com/a/42304034)

| Parameter name | Description | How get it| Example of the value |
| --- | --- | --- | --- |
| `reddit_id` | The Client ID generated from the apps page | [Official guide](https://github.com/reddit-archive/reddit/wiki/OAuth2#authorization-implicit-grant-flow) | 40oK80pF8ac3Cn |
| `reddit_secret` | The secret generated from the apps page | Copy the value as showed [here](https://github.com/reddit-archive/reddit/wiki/OAuth2#getting-started) | 9KEUOE7pi8dsjs9507asdeurowGCcg|
| `reddit_username` | The reddit account name| The name you use for log in | pistoSniffer |

## :arrow_down: Output

A new folder with two csv files are created from `dataset_builder.py`, the script have some features:

- Remove rows with same `id`
- Have a `caching_size` parameter to don't store all dataset in RAM

They have the following structure:

#### submissions.csv

Each row is a submission of a specific subreddit and `id` field is unique across the dataset (PK).

| Column name | Description                          | Example                                                                |
|-------------|--------------------------------------|------------------------------------------------------------------------|
| subreddit   | Name of the subreddit                | MTB                                                                    |
| id          | Unique identifier of the submission  | lhr2bo                                                                 |
| created_utc | UTC when submission was created      | 1613068060                                                             |
| title       | Title of the submission              | Must ride So...                                                        |
| selftext    | Text off the submission              | What are the best trails to ride in...                                 |
| full_link   | Reddit unique link to the submission | https://www.reddit.com/r/MTB/comments/lhr2bo/must_ride_so_cali_trails/ |

#### comments.csv

Each row is a comment under a submission of a specific subreddit and `id` field is unique across the dataset (PK).

| Column name | Description                          | Example                                                                          |
|-------------|--------------------------------------|----------------------------------------------------------------------------------|
| subreddit   | Name of the subreddit                | News                                                                             |
| id          | Unique identifier of the comment     | gmz45xo                                                                          |
| submission_id | Id of the comment main submission  | lhr2bo                                                                          |
| body        | Text of the comment                  | We're past the point...                                                          |
| created_utc | UTC when comment was created         | 1613072734                                                                       |
| parent_id   | Id of the parent in a tree structure | t3_lhssi4                                                                        |
| permalink   | Reddit unique link to the comment    | /r/news/comments/lhssi4/air_force_wants_to_know_if_key_pacific_airfield/gmz45xo/ |

---

## :book: Glossary

- _subreddit_: section of reddit website focused on a particular topic

- _submission_: the post that appear in each subreddit. When you open a subreddit page, all the posts you see. Each
  submission has a tree of _comments_

- _comment_: text wrote by a reddit user under a _submission_ inside a _subreddit_
    - The main goal of this repository is to gather the _comments_ belong to the _subreddit_

## :writing_hand: Notes

- Under the hood the script use [pushshift](https://pushshift.io/api-parameters/) to gather submissions id,
  and [praw](https://praw.readthedocs.io/en/latest/)
  for collect the submissions comments
    - With this approach we require fewer data to [pushshift](https://pushshift.io/api-parameters/)
    - Due to the usage of [praw](https://praw.readthedocs.io/en/latest/) API, the reddit credentials are required
- More info about the `subreddit_downloader.py` script under the `--help` command:
- Other packages:
    - [psaw](https://github.com/dmarx/psaw): Python Pushshift.io API Wrapper
- [?] Data empty CSV:
    - Sometimes we have an empty csv under `/data/<subreddit>/<timestamp>/comments/xxx.csv`
    - This behaviour is due of a batch of _submissions_ that don't have comments, you can check this opening the
      `/data/<subreddit>/<timestamp>/submissions/xxx.csv` equivalent file (same `xxx.csv` name) and open the submission
      link

```bash
python src/subreddit_downloader.py --help
Usage: subreddit_downloader.py [OPTIONS] SUBREDDIT

  Download all the submissions and relative comments from a subreddit.

Arguments:
  SUBREDDIT  The subreddit name  [required]

Options:
  --output-dir TEXT               Optional output directory  [default:
                                  ./data/]

  --batch-size INTEGER            Request `batch_size` submission per time
                                  [default: 10]

  --laps INTEGER                  How many times request `batch_size` reddit
                                  submissions  [default: 3]

  --reddit-id TEXT                Reddit client_id, visit
                                  https://github.com/reddit-
                                  archive/reddit/wiki/OAuth2  [required]

  --reddit-secret TEXT            Reddit client_secret, visit
                                  https://github.com/reddit-
                                  archive/reddit/wiki/OAuth2  [required]

  --reddit-username TEXT          Reddit username, used for build the
                                  `user_agent` string, visit
                                  https://github.com/reddit-
                                  archive/reddit/wiki/API  [required]

  --utc-after TEXT                Fetch the submissions after this UTC date
  --utc-before TEXT               Fetch the submissions before this UTC date
  --debug / --no-debug            Enable debug logging  [default: False]
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.

  --help                          Show this message and exit.
```

## :zzz: TODO

**dataset_builder.py**

- [ ] store some dataset info (subreddit, max/min utc/human, n^ lines)

**subreddit_downloader.py**

- [ ] load user credentials in `subreddit_downloader.py` from local config file
- [ ] store/log the utc and human datetime
- [ ] use case: download all data from X datetime until now
    - [ ] early stopping if no new data fetched
- [ ] refactory of `dataset_builder.py:_rows_parser`: find a more efficient approach to check `id` duplicates
    - [ ] maybe switch to use pandas as matrix manager
- [ ] should switch to use [psaw](https://github.com/dmarx/psaw)?