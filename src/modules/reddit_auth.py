import os
import sys
import configparser
import praw
from prawcore.exceptions import OAuthException, ResponseException
import tkinter as tk
from modules.gui import CredentialsInputGUI
from modules.oauth_handler import RedditOAuth


class RedditAuth:
    """
    A class to handle Reddit authentication using PRAW.

    This class manages the reading of Reddit API credentials from a file or user input,
    and creates an authenticated Reddit instance.
    """

    def __init__(self, is_exe: bool = False, file_path: str = "reddit_credentials.ini", user_agent: str = "ereddicator") -> None:
        """
        Initialise the RedditAuth instance.

        Args:
            is_exe (bool): Flag to determine if running as an executable. Defaults to False.
            file_path (str): Path to the credentials file. Defaults to "reddit_credentials.ini".
            user_agent (str): User agent string for Reddit API. Defaults to "ereddicator".
        """
        self.is_exe = is_exe
        self.file_path = file_path
        self.user_agent = user_agent
        self.client_id = None
        self.client_secret = None
        self.username = None
        self.password = None
        self.two_factor_code = None
        self.refresh_token = None
        self.use_oauth = False

    def _read_credentials(self) -> None:
        """
        Read credentials either from user input or from a file.

        This method calls either _prompt_credentials or _read_credentials_from_file
        based on the is_exe flag.
        """
        if self.is_exe:
            self._prompt_credentials_from_gui()
        else:
            self._read_credentials_from_file()

    def _prompt_credentials_from_gui(self) -> None:
        """
        Prompt the user to input Reddit API credentials using a graphical user interface.

        This method creates a Tkinter window with input fields for the client ID, client secret,
        username, password, and 2FA code (optional). It uses the CredentialsInputGUI class
        to manage the input process.
        """
        root = tk.Tk()
        gui = CredentialsInputGUI(root)
        credentials = gui.get_credentials()
        root.destroy()  # Ensure the window is destroyed after getting credentials
        
        self.client_id = credentials["client id"]
        self.client_secret = credentials["client secret"]

        if credentials.get("oauth_mode", False):
            self.use_oauth = True
            try:
                print("Starting OAuth authorisation flow...")
                oauth = RedditOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )

                self.username, self.refresh_token = oauth.perform_oauth_flow()
                print(f"Successfully authenticated as {self.username} using OAuth.")
            except Exception as e:
                print(f"OAuth authentication failed: {e}")
                sys.exit(1)
        else:
            self.username = credentials["username"]
            self.password = credentials["password"]
            self.two_factor_code = credentials.get("two factor code", "None")

    def _read_credentials_from_file(self) -> None:
        """
        Read Reddit API credentials from a file.

        This method is called when Ereddicator is running as a Python script. It
        reads the credentials from the file specified by self.file_path.

        Raises:
            FileNotFoundError: If the credentials file is not found.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Credentials file not found: {self.file_path}")

        config = configparser.ConfigParser(interpolation=None)
        with open(self.file_path, "r", encoding="utf-8") as file:
            config.read_file(file)

        self.client_id = config["reddit"]["client_id"].strip()
        self.client_secret = config["reddit"]["client_secret"].strip()

        # Check if we have a refresh token or plan to use OAuth
        if "refresh_token" in config["reddit"]:
            self.refresh_token = config["reddit"]["refresh_token"]
            self.use_oauth = True
            # Username might be stored if we've authenticated before
            if "username" in config["reddit"]:
                self.username = config["reddit"]["username"]
                print(f"Using stored refresh token for {self.username}")
            else:
                print("Refresh token found, will fetch username during authentication")
        # Check for OAuth mode without refresh token (first-time setup)
        elif "username" not in config["reddit"] and "password" not in config["reddit"]:
            print("OAuth mode detected (no username/password provided)")
            self.use_oauth = True
            try:
                print("Starting OAuth authorization flow...")
                oauth = RedditOAuth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                self.username, self.refresh_token = oauth.perform_oauth_flow()

                # Save the refresh token for future use
                config["reddit"]["username"] = self.username
                config["reddit"]["refresh_token"] = self.refresh_token
                with open(self.file_path, "w") as f:
                    config.write(f)

                print(f"Successfully authenticated as {self.username}")
                print(f"Refresh token saved to {self.file_path}")
            except Exception as e:
                print(f"OAuth authentication failed: {e}")
                sys.exit(1)
        else:
            # Traditional username/password authentication
            self.username = config["reddit"]["username"].strip()
            self.password = config["reddit"]["password"].strip()
            if "two_factor_code" in config["reddit"]:
                self.two_factor_code = config["reddit"]["two_factor_code"].strip()
            else:
                self.two_factor_code = "None"

    def get_reddit_instance(self) -> praw.Reddit:
        """
        Create and return an authenticated Reddit instance.

        This method reads the credentials if they haven't been set,
        creates a Reddit instance, and verifies the authentication. It
        will cause a SystemExit if any errors occur.

        Returns:
            praw.Reddit: An authenticated Reddit instance.

        Raises:
            FileNotFoundError: If the credentials file is not found.
            OAuthException: If authentication fails due to OAuth issues.
            ResponseException: If there's an issue with the Reddit API response.
        """
        try:
            if not (self.client_id and self.client_secret and (self.username or self.refresh_token)):
                self._read_credentials()
            
            print("Retrieving Reddit Authentication instance...")

            if self.use_oauth and self.refresh_token:
                reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    refresh_token=self.refresh_token,
                    user_agent=self.user_agent
                )
                # If username wasn't provided, get it from the API
                if not self.username:
                    self.username = reddit.user.me().name
                    print(f"Successfully authenticated as {self.username} using OAuth.")
                # Only show success message if not already shown in prompt_credentials
                elif not self.is_exe:
                    print(f"Successfully authenticated as {self.username} using OAuth.")
            else:
                if self.two_factor_code and self.two_factor_code != "None":
                    self.two_factor_code = self.two_factor_code.replace(" ", "")
                    password = f"{self.password}:{self.two_factor_code}"
                else:
                    password = self.password

                reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    username=self.username,
                    password=password,
                    user_agent=self.user_agent
                )
                print(f"Successfully authenticated as {self.username}.")

            # Verify authentication worked
            reddit.user.me()

            return reddit

        except FileNotFoundError:
            print(f"Please create a file named '{self.file_path}' in the same directory "
                  "as main.py with one of the following formats:\n\n"
                  "For traditional Reddit accounts:\n"
                  "[reddit]\n"
                  "client_id = YOUR_CLIENT_ID\n"
                  "client_secret = YOUR_CLIENT_SECRET\n"
                  "username = YOUR_USERNAME\n"
                  "password = YOUR_PASSWORD\n"
                  "# Leave as None if you don't use two-factor authentication\n"
                  "two_factor_code = None\n\n"
                  "For Reddit accounts that use Google login (or other OAuth methods):\n"
                  "[reddit]\n"
                  "client_id = YOUR_CLIENT_ID\n"
                  "client_secret = YOUR_CLIENT_SECRET\n"
                  "# The refresh_token will be filled in automatically after your first login")
            sys.exit(1)
        except (OAuthException, ResponseException) as e:
            print("Failed to authenticate with Reddit. Please check your credentials.")
            print(f"Error details: {e}")
            sys.exit(1)
