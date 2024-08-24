import os
import sys
import configparser
import praw
from prawcore.exceptions import OAuthException, ResponseException


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

    def _read_credentials(self) -> None:
        """
        Read credentials either from user input or from a file.

        This method calls either _prompt_credentials or _read_credentials_from_file
        based on the is_exe flag.
        """
        if self.is_exe:
            self._prompt_credentials()
        else:
            self._read_credentials_from_file()

    def _prompt_credentials(self) -> None:
        """
        Prompt the user to input Reddit API credentials.

        This method is called when Ereddicator is running as an executable.
        """
        print("Please enter your Reddit API credentials. Please see the README.md file if you need help.")
        self.client_id = input("Client ID: ").strip()
        self.client_secret = input("Client Secret: ").strip()
        self.username = input("Username: ").strip()
        self.password = input("Password: ").strip()

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

        config = configparser.ConfigParser()
        config.read(self.file_path)

        self.client_id = config["reddit"]["client_id"]
        self.client_secret = config["reddit"]["client_secret"]
        self.username = config["reddit"]["username"]
        self.password = config["reddit"]["password"]

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
            if not all([self.client_id, self.client_secret, self.username, self.password]):
                self._read_credentials()
            
            print("Retrieving Reddit Authentication instance...")

            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent=self.user_agent
            )
            reddit.user.me()  # Won't throw exceptions if authentication succeeded.
            return reddit
        except FileNotFoundError:
            print(f"Please create a file named '{self.file_path}' in the same directory "
                  "as main.py with the following format:\n"
                  "[reddit]\nclient_id = YOUR_CLIENT_ID\nclient_secret = YOUR_CLIENT_SECRET\n"
                  "username = YOUR_USERNAME\npassword = YOUR_PASSWORD")
            sys.exit(1)
        except (OAuthException, ResponseException) as e:
            print("Failed to authenticate with Reddit. Please check your credentials.")
            print(f"Error details: {e}")
            sys.exit(1)
