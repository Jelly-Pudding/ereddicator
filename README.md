# Ereddicator
This Python script allows you to delete all your Reddit comments, posts, saved items, upvotes, downvotes, and hidden posts. However, upvotes and downvotes on archived posts will remain. There is no way to undo them. You can disable "make my votes public" in your preferences: https://www.reddit.com/prefs/

Note: The script replaces each comment and post with random text before deletion as an added measure against the original content being read.

## Instructions (for Windows Users)
If you don't want to install Python, you can use the `.exe` version of the script:

1. Obtain a `client_id` and `client_secret` and save these in a notepad file:
- Go to https://www.reddit.com/prefs/apps
- Click "Create App" or "Create Another App"
- Choose "script" for personal use
- Fill in any name and for the redirect uri put http://localhost:8080
- After creation, the client_id is the string under "personal use script"
- The client_secret is labeled "secret"
2. Download the latest `.zip` file from the [Releases](https://github.com/Jelly-Pudding/ereddicator/releases/) page.
3. Extract the contents of the `.zip` file to a folder.
6. Run the `ereddicator.exe` file by double-clicking it. A console window will open. Follow its instructions.

## Instructions (for Python Users)

### Installation
1. Git clone this repository: `git clone https://github.com/Jelly-Pudding/ereddicator.git`
2. Install this specific version of PRAW (Python Reddit API Wrapper):
`pip install praw==7.7.1`

### Instructions
1. Obtain a `client_id` and `client_secret`:
- Go to https://www.reddit.com/prefs/apps
- Click "Create App" or "Create Another App"
- Choose "script" for personal use
- Fill in any name and for the redirect uri put http://localhost:8080
- After creation, the client_id is the string under "personal use script"
- The client_secret is labeled "secret"
2. Create a file named `reddit_credentials.ini` in the same directory as the script.
3. Add your Reddit API credentials to the file in the following format:
    ```
    [reddit]
    client_id = YOUR_CLIENT_ID
    client_secret = YOUR_CLIENT_SECRET
    username = YOUR_USERNAME
    password = YOUR_PASSWORD
    ```
4. Run the script using Python: `python ereddicator.py`.

## Generating the EXE File
Run this:
`pyinstaller --onefile --console ereddicator.py`

`praw.ini` needs to be in the same directory as the `.exe` file generated from the above command. Its content:

```
[DEFAULT]
# A boolean to indicate whether or not to check for package updates.
check_for_updates=False

# Object to kind mappings
comment_kind=t1
message_kind=t4
redditor_kind=t2
submission_kind=t3
subreddit_kind=t5
trophy_kind=t6

# The URL prefix for OAuth-related requests.
oauth_url=https://oauth.reddit.com

# The amount of seconds of ratelimit to sleep for upon encountering a specific type of 429 error.
ratelimit_seconds=5

# The URL prefix for regular requests.
reddit_url=https://www.reddit.com

# The URL prefix for short URLs.
short_url=https://redd.it

# The timeout for requests to Reddit in number of seconds
timeout=16
```
