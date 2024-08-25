# Ereddicator

This Python script allows you to delete all your Reddit comments, posts, saved items, upvotes, downvotes, and hidden posts. However, upvotes and downvotes on archived posts will remain. There is no way to undo them. You can disable "make my votes public" in your preferences: https://www.reddit.com/prefs/

## Features

- **Selective Content Removal**: Choose which types of content to delete. Options include:
  - Comments
  - Posts
  - Saved items
  - Upvoted content
  - Downvoted content
  - Hidden posts
- **Karma Threshold**: You can now set karma thresholds for comments and posts. Content with karma above or equal to the threshold will be preserved.
- **Advertise Option**: When enabled, there's a 50% chance for each comment or post to be replaced with an advertisement for Ereddicator instead of random text before deletion.

Note: The content replacement (with either random text or an advertisement) occurs immediately before deletion as an added measure against the original content being read.

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
4. Run the `ereddicator.exe` file by double-clicking it. You may see `Windows protected your PC`. Just click on `More Info` and then click `Run anyway`. 
5. A GUI window will open. Enter your Reddit API credentials when prompted.
6. In the main window, configure your preferences:
   - Select which types of content to delete
   - Set karma thresholds for comments and posts (use "*" to delete all)
   - Choose whether to enable the Ereddicator advertisement option
     (When enabled, there's a 50% chance for each comment/post to be replaced with an ad instead of random text before deletion)
7. Click "Start Content Removal" to begin the process.

## Instructions (for Python Users)

### Installation

1. Git clone this repository: `git clone https://github.com/Jelly-Pudding/ereddicator.git`
2. Install this specific version of PRAW (Python Reddit API Wrapper):
   `pip install praw==7.7.1`

### Instructions

1. Obtain a `client_id` and `client_secret` as described in the Windows instructions above.
2. Create a file named `reddit_credentials.ini` in the same directory as the script.
3. Add your Reddit API credentials to the file in the following format:
    ```
    [reddit]
    client_id = YOUR_CLIENT_ID
    client_secret = YOUR_CLIENT_SECRET
    username = YOUR_USERNAME
    password = YOUR_PASSWORD
    ```
4. Navigate to the `src` directory.
5. Run the script using Python: `python main.py`.
6. Follow the on-screen instructions in the GUI to configure your preferences and start the content removal process.

## Generating the EXE File

1. Navigate to the `src` directory of the project:
   ```
   cd path/to/ereddicator/src
   ```

2. Run the following PyInstaller command:
   ```
   python -m PyInstaller --onefile --console --name ereddicator --add-data "modules:modules" main.py
   ```

   This command does the following:
   - `--onefile`: Creates a single executable file.
   - `--console`: Keeps the console window open (useful for seeing any error messages).
   - `--name ereddicator`: Names the output executable 'ereddicator'.
   - `--add-data "modules:modules"`: Includes the `modules` directory in the executable.

3. After the process completes, you'll find the `ereddicator.exe` file in the `dist` directory.

4. Create a file called `praw.ini` in the same directory as the `ereddicator.exe` file. The content of `praw.ini` should be:

   ```ini
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

5. The `ereddicator.exe` file is now ready to be distributed and used.

Note: Make sure you have PyInstaller installed (`pip install pyinstaller`) before running the command.