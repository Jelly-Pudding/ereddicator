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
- **Edit-Only Mode**: For comments and posts, you can choose to only edit the content without deleting it. This may be desirable as Reddit is capable of restoring deleted comments. It may also be desirable as web crawlers that picked up your original content may overwrite it with the new text.
- **Karma Threshold**: You can set karma thresholds for comments and posts. Content with karma above or equal to the threshold will be preserved.
- **Preserve Gilded Content**: Option to preserve comments and posts that have been gilded (received Reddit gold).
- **Preserve Distinguished Content**: Option to preserve comments and posts that have been distinguished by moderators.
- **Subreddit Filtering**:
  - Whitelist: Specify subreddits to exclude from processing.
  - Blacklist: Specify subreddits to exclusively process, ignoring all others.
- **Date Range Filtering**: Set a specific date range to process content from, allowing you to target content from a particular time period.
- **Dry Run Mode**: Simulate the removal process without actually making any changes. In this mode, Ereddicator will print out what actions would be taken (e.g. what comments and posts will be deleted) without modifying any of your Reddit content.
- **Custom Replacement Text**: Specify custom text to replace your content during editing or before deletion. If not provided, random text will be used.
- **Advertise Option**: When enabled, there's a 50% chance for each comment or post to be replaced with an advertisement for Ereddicator instead of random text or custom text.

Note: As an added measure against the original content being read, the content replacement process (with either random text or an advertisement) occurs three times immediately before the final edit or deletion.

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
   * If you use Two-Factor Authentication, enter your 2FA code in the "Two Factor Code" field. If you don't use 2FA, leave this field as is.
6. After you successfully authenticate, a new window opens. In this window, you can configure your preferences.
7. Click "Start Content Removal" to begin the process.

## Instructions (for Python Users)

### Installation

1. Git clone this repository: `git clone https://github.com/Jelly-Pudding/ereddicator.git`
2. Navigate to the project directory:
   ```
   cd ereddicator
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

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
   # Leave as None if you don't use two-factor authentication
   two_factor_code = None
   ```
   If you use 2FA, replace None with your 2FA code.
4. Navigate to the `src` directory.
5. Run the script using Python: `python main.py`.
6. Follow the on-screen instructions in the GUI to configure your preferences and start the content removal process.

## Support Me
Donations will help me with the development of this project.

One-off donation: https://ko-fi.com/lolwhatyesme

Patreon: https://www.patreon.com/lolwhatyesme
