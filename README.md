# Ereddicator
This Python script allows you to delete all your Reddit comments, posts, saved items, upvotes, downvotes, and hidden posts. However, upvotes and downvotes on archived posts will remain. There is no way to undo them. You can disable "make my votes public" in your preferences: https://www.reddit.com/prefs/

Note: The script replaces each comment and post with random text before deletion as an added measure against the original content being read.

## Instructions (for Windows Users)
If you don't want to install Python, you can use the `.exe` version of the script:

1. Download the latest `.zip` file from the [Releases](https://github.com/yourusername/repositoryname/releases) page.
2. Extract the contents of the `.zip` file to a folder.
3. Open the `reddit_credentials.ini` file in a text editor.
4. Add your Reddit API credentials to the file in the following format:
    ```
    [reddit]
    client_id = YOUR_CLIENT_ID
    client_secret = YOUR_CLIENT_SECRET
    username = YOUR_USERNAME
    password = YOUR_PASSWORD
    ```
5. Save the `reddit_credentials.ini` file.
6. Run the `ereddicator.exe` file by double-clicking it. A console window will open, and the script will start running.

**Note**: If you encounter any issues, make sure that your credentials in the `reddit_credentials.ini` file are correct.

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
