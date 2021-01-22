# subreddit-text-downloader

<a href="https://gitmoji.carloscuesta.me">
  <img src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=flat-square" alt="Gitmoji">
</a>

> Download all the text comments from a subreddit

Use the
script [subreddit_downloader.py](https://github.com/pistocop/reddit-downloader/blob/main/src/subreddit_downloader.py)
multiple times to download the data, <br>
and then run the
script [dataset_builder.py](https://github.com/pistocop/reddit-downloader/blob/main/src/dataset_builder.py) for create a
unique dataset.

## :rocket: Usage

Basic usage to download submissions and relative comments from
subreddit [AskReddit](https://www.reddit.com/r/AskReddit/) and [News](https://www.reddit.com/r/news/):

```shell
# Install the dependencies
pip install -r requirements.txt

# Download the AskReddit comments of the last 30 submissions
python src/subreddit_downloader.py AskReddit --batch-size 10 --laps 3 --reddit-id <reddit_id> --reddit-secret <reddit_secret> --reddit-username <reddit_username>

# Download the News comments after 1 January 2021
python src/subreddit_downloader.py AskReddit --batch-size 512 --laps 3 --reddit-id <reddit_id> --reddit-secret <reddit_secret> --reddit-username <reddit_username> --utc-after 1609459200

# Build the dataset and check the results under `./dataset/` path
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

## :book: Glossary

- _subreddit_: section of reddit website focused on a particular topic

- _submission_: the post that appear in each subreddit. When you open a subreddit page, all the posts you see. Each
  submission has a tree of _comments_

- _comment_: text wrote by a reddit user under a _submission_ inside a _subreddit_
    - The main goal of this repository is sto gather the _comments_ belong to the _subreddit_

## :writing_hand: Notes

- Under the hood the script use [pushshift](https://pushshift.io/api-parameters/) to gather submissions id,
  and [praw](https://praw.readthedocs.io/en/latest/)
  for collect the submissions comments
    - With this approach we require fewer data to [pushshift](https://pushshift.io/api-parameters/)
    - Due to the usage of [praw](https://praw.readthedocs.io/en/latest/) API, the reddit credentials are required
- More info about the `subreddit_downloader.py` script under the `--help` command:

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

- [ ] store/log the utc and human datetime
- [ ] use case: download all data from X datetime until now
    - [ ] early stopping if no new data fetched
