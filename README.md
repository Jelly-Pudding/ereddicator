# Ereddicator

This Python script allows you to edit and/or delete all your Reddit comments, posts, saved items, upvotes, downvotes, and hidden posts. However, upvotes and downvotes on archived posts will remain. There is no way to undo them. You can disable "make my votes public" in your preferences: https://www.reddit.com/prefs/

## Contents

- [Features](#features)
- [Reddit Data Export Request](#reddit-data-export-request)
- [Instructions (for Windows Users)](#instructions-for-windows-users)
- [Instructions (for Python Users)](#instructions-for-python-users)
  - [Installation](#installation)
  - [Instructions](#instructions)
- [Support Me](#buy-me-a-coffee)

## Features

- **Selective Content Removal**: Choose which types of content to delete. Options include:
  - Comments
  - Posts
  - Saved items
  - Upvoted content
  - Downvoted content
  - Hidden posts
- **Reddit Data Export Support**: You can process content from Reddit's data export. Although it requires more effort on your part, it is ***highly recommended*** you take advantage of this feature as it ensures all of your content is processed. See [Reddit Data Export Request](#reddit-data-export-request) for instructions.
- **OAuth Authentication Support**: For users who log in to Reddit via Google ("Login with Google"), you can authenticate via OAuth.
- **Edit-Only Mode**: For comments and posts, you can choose to only edit the content without deleting it. This is ***highly recommended*** for a couple of reasons:
  - Reddit is capable of restoring deleted content, but if you edit content first and leave it edited for some time, any future restoration would likely recover the edited version rather than the original content.
  - Web crawlers and archives that previously captured your content may overwrite their records with your edited version.
- **Delete-Only Mode**: For comments and posts, you can choose to directly delete content without editing it first. This can be useful if you want to avoid potential auto-moderator actions that might be triggered by edited content. Some subreddits may have auto-moderators configured to take action on edited content which could result in unwanted bans.
- **Karma Threshold**: You can set karma thresholds for comments and posts. Content with karma above or equal to the threshold will be preserved.
- **Preserve Gilded Content**: Option to preserve comments and posts that have been gilded (received Reddit gold).
- **Preserve Distinguished Content**: Option to preserve comments and posts that have been distinguished by moderators.
- **Subreddit Filtering**:
  - Whitelist: Specify subreddits to exclude from processing.
  - Blacklist: Specify subreddits to exclusively process, ignoring all others.
- **Date Range Filtering**: Set a specific date range to process content from, allowing you to target content from a particular time period.
- **Dry Run Mode**: Simulate the removal process without actually making any changes. In this mode, Ereddicator will print out what actions would be taken (e.g. what comments and posts will be deleted) without modifying any of your Reddit content.
- **Custom Replacement Text**: Specify custom text to replace your content during editing or before deletion. If not provided, random text will be used.
- **Persistent Processing**: Tracks which items have already been processed across multiple runs, ensuring that items are not processed again if the script is restarted or interrupted.
- **Advertise Option**: When enabled, there's a 50% chance for each comment or post to be replaced with a simple message mentioning Ereddicator instead of random text or custom text.

## Reddit Data Export Request
Reddit's API is limited and sometimes does not retrieve all comments and posts. If you want to ensure you get everything, you will need to make a Reddit data export request:

1. Go to https://www.reddit.com/settings/data-request
2. Fill in the form:
   * Select the appropriate request type based on your location:
      * If you're in the EU/UK: Select "General Data Protection Regulation (GDPR)"
      * If you're in California: Select "California Consumer Privacy Act (CCPA)"
      * For all other locations: Select "Other"
   * For date range, select "I want data from my full time at Reddit"
3. Submit the request.

Reddit will process your request and send a message to your Reddit inbox (it is very fast usually and takes minutes, but it can take 1-2 days). The message will contain a download link. Extract the contents of the `.zip` file to a folder. You will then be able to select this folder when [using Ereddicator](#instructions-for-windows-users) (look for the `Reddit Export Directory` option).

## Instructions (for Windows Users)

If you don't want to install Python, you can use the `.exe` version of the script:

1. **Optional First Step** - Make a Reddit data request ([see here for instructions](#reddit-data-export-request)). While Ereddicator works without this, using Reddit's data export ensures all of your content is processed.
2. Obtain a `client_id` and `client_secret` and save these in a notepad file:
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App".
   - You can name it anything. It does not matter.
   - Choose "script" for personal use.
   - For the "redirect uri", put http://localhost:8080

   ![Creating Reddit App](images/create-app.png)

   - After creation, the client_id is the string under "personal use script". For example, it may look like this: "AE9-zURLEvI1pze_rqH4Iw".
   - The client_secret is what appears next to "secret". It will look like this: "ZeqnEO_F21BrzzgOpb_es4kOfbhTww"

   ![Finding Client ID and Secret](images/client-id-and-secret.png)

3. Download the latest `.zip` file from the [Releases](https://github.com/Jelly-Pudding/ereddicator/releases/) page.
4. Extract the contents of the `.zip` file to a folder.
5. Run the `ereddicator.exe` file by double-clicking it. You may see `Windows protected your PC`. Just click on `More Info` and then click `Run anyway`. 
6. A terminal window will open. **Keep this terminal window open and visible throughout the entire process.** This terminal displays authentication status, error messages, and progress updates. Do not close or minimise it.
7. A GUI window will also open. Enter your Reddit API credentials into it.
   * **For traditional Reddit accounts**:
     * If you use Two-Factor Authentication, enter your 2FA code in the "Two Factor Code" field. If you don't use 2FA, leave this field as is.
     * Enter your client_id, client_secret, username, and password.
   * **For users who use Reddit's "Login with Google"**:
     * Select the "OAuth (Google Login)" option at the top
     * Enter your `client_id` and `client_secret`
     * Click "Authorise with Reddit" - this will open a browser window
     * Log in to Reddit through Google in the browser and authorise the application
     * Once authorised, you'll be redirected back to Ereddicator
8. After you successfully authenticate, a new window opens. In this window, you can configure your preferences.
9. Click "Start Content Removal" to begin the process. If you cannot see this button, then try to resize the window to make it bigger.

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

1. **Optional First Step** - Make a Reddit data request ([see here for instructions](#reddit-data-export-request)). While Ereddicator works without this, using Reddit's data export ensures all of your content is processed.
2. Obtain a `client_id` and `client_secret` and save these in a notepad file:
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App".
   - You can name it anything. It does not matter.
   - Choose "script" for personal use.
   - For the "redirect uri", put http://localhost:8080

   ![Creating Reddit App](images/create-app.png)

   - After creation, the client_id is the string under "personal use script". For example, it may look like this: "AE9-zURLEvI1pze_rqH4Iw".
   - The client_secret is what appears next to "secret". It will look like this: "ZeqnEO_F21BrzzgOpb_es4kOfbhTww"

   ![Finding Client ID and Secret](images/client-id-and-secret.png)

3. Create a file named `reddit_credentials.ini` in the same directory as the script.
4. Add your Reddit API credentials to the file in one of the following formats:

   **For traditional Reddit accounts:**
   ```
   [reddit]
   client_id = YOUR_CLIENT_ID
   client_secret = YOUR_CLIENT_SECRET
   username = YOUR_USERNAME
   password = YOUR_PASSWORD
   # Leave as None if you don't use two-factor authentication
   two_factor_code = None
   ```
   **For Reddit accounts that use Google login:**
   ```
   [reddit]
   client_id = YOUR_CLIENT_ID
   client_secret = YOUR_CLIENT_SECRET
   # The refresh_token will be filled in after your first login
   ```
5. Navigate to the `src` directory.
6. Run the script using Python: `python main.py`.
7. Keep the terminal where you ran the Python command visible throughout the entire process. This terminal displays authentication status, error messages, and progress updates.
8. If you're using Google login, you'll be prompted to authorise via a browser. After successful authorisation, the refresh token will be saved for future use.
9. Follow the on-screen instructions in the GUI to configure your preferences and start the content removal process.

## Buy Me a Coffee
[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/K3K715TC1R)
