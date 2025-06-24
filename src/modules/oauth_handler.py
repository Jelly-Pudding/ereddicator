import webbrowser
import socket
import http.server
import socketserver
import urllib.parse
import threading
import time
import json
import requests
from typing import Optional, Dict, Tuple


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """
    HTTP request handler for OAuth callback.
    Captures the authorisation code from Reddit's redirect.
    """

    def do_GET(self):
        """Handle GET requests to capture the authorisation code."""
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

        if 'code' in query_components:
            self.server.authorisation_code = query_components['code'][0]

            # Send a response to the browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html_content = """
            <html>
            <head>
                <title>Authorisation Received</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
                    .processing { color: #2196F3; font-size: 24px; margin-bottom: 20px; }
                    .info { margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <div class="processing">Authorisation Received.</div>
                <div class="info">Reddit has authorised Ereddicator. Please wait while we complete the authentication process.</div>
                <div class="info">You can close this window and return to Ereddicator to see the results.</div>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode())
        else:
            # Error in the OAuth flow
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            error_message = query_components.get('error', ['Unknown error'])[0]
            html_content = f"""
            <html>
            <head>
                <title>Authentication Failed</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                    .error {{ color: #f44336; font-size: 24px; margin-bottom: 20px; }}
                    .info {{ margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="error">Authentication Failed</div>
                <div class="info">Error: {error_message}</div>
                <div class="info">Please close this window and try again.</div>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode())

    def log_message(self, format, *args):
        """Suppress server logs."""
        return


class OAuthServer:
    """
    A simple HTTP server to handle the OAuth callback.
    """
    def __init__(self, port: int = 8080):
        """
        Initialise the OAuth server.

        Args:
            port (int): The port to listen on. Defaults to 8080.
        """
        self.port = port
        self.server = None
        self.thread = None
        self.authorisation_code = None

    def start(self) -> None:
        """Start the server in a new thread."""
        class OAuthHTTPServer(socketserver.TCPServer):
            allow_reuse_address = True
            authorisation_code = None

        self.server = OAuthHTTPServer(("localhost", self.port), OAuthCallbackHandler)
        self.server.timeout = 0.5  # Check for shutdown flag every half second

        def run_server():
            while not getattr(self.thread, "stop_flag", False):
                self.server.handle_request()
                if self.server.authorisation_code:
                    break

        self.thread = threading.Thread(target=run_server)
        self.thread.daemon = True
        self.thread.start()

    def stop(self) -> None:
        """Stop the server."""
        if self.thread and self.thread.is_alive():
            self.thread.stop_flag = True
            self.thread.join(1.0)  # Wait for the server thread to finish

        if self.server:
            self.server.server_close()

    def get_authorisation_code(self) -> Optional[str]:
        """Get the authorisation code received from Reddit."""
        if self.server:
            return self.server.authorisation_code
        return None


class RedditOAuth:
    """
    Handles the OAuth flow for Reddit authentication.
    """
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "http://localhost:8080",
                 user_agent: str = "ereddicator"):
        """
        Initialise the Reddit OAuth handler.

        Args:
            client_id (str): Reddit API client ID.
            client_secret (str): Reddit API client secret.
            redirect_uri (str, optional): Redirect URI for OAuth flow. Defaults to "http://localhost:8080".
            user_agent (str, optional): User agent for API requests. Defaults to "ereddicator".
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.user_agent = user_agent

    def get_auth_url(self, scopes: list = None, state: str = "ereddicator", duration: str = "permanent") -> str:
        """
        Generate the authorisation URL.

        Args:
            scopes (list, optional): List of requested permissions. Defaults to ["identity", "edit", "history",
                                    "read", "vote", "save"].
            state (str, optional): State parameter for OAuth. Defaults to "ereddicator".
            duration (str, optional): Token duration. Defaults to "permanent".

        Returns:
            str: The authorisation URL to send the user to.
        """
        if scopes is None:
            scopes = ["identity", "edit", "history", "read", "vote", "save"]

        scope_str = " ".join(scopes)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "state": state,
            "redirect_uri": self.redirect_uri,
            "duration": duration,
            "scope": scope_str
        }

        query_string = "&".join([f"{key}={urllib.parse.quote(value)}" for key, value in params.items()])
        return f"https://www.reddit.com/api/v1/authorize?{query_string}"

    def get_tokens(self, code: str) -> Dict[str, str]:
        """
        Exchange an authorisation code for access and refresh tokens.

        Args:
            code (str): The authorisation code from Reddit.

        Returns:
            Dict[str, str]: Dictionary containing the access_token and refresh_token.

        Raises:
            Exception: If token exchange fails.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }

        auth = (self.client_id, self.client_secret)
        headers = {"User-Agent": self.user_agent}

        response = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            data=data,
            auth=auth,
            headers=headers
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get tokens: {response.text}")

        token_data = response.json()
        return {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token")
        }

    def get_username(self, access_token: str) -> str:
        """
        Get the username associated with an access token.

        Args:
            access_token (str): The OAuth access token.

        Returns:
            str: The username.

        Raises:
            Exception: If the request fails.
        """
        headers = {
            "authorization": f"bearer {access_token}",
            "User-Agent": self.user_agent
        }

        response = requests.get(
            "https://oauth.reddit.com/api/v1/me",
            headers=headers
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get username: {response.text}")

        user_data = response.json()
        return user_data.get("name")

    def perform_oauth_flow(self) -> Tuple[str, str]:
        """
        Perform the complete OAuth flow.

        Returns:
            Tuple[str, str]: A tuple containing (username, refresh_token).

        Raises:
            Exception: If any part of the OAuth flow fails.
        """
        # Start the local server to receive the callback
        server = OAuthServer()
        server.start()

        try:
            # Generate and open the authorisation URL
            auth_url = self.get_auth_url()
            webbrowser.open(auth_url)

            # Wait for the authorisation code (timeout after 5 minutes)
            start_time = time.time()
            while not server.get_authorisation_code() and time.time() - start_time < 300:
                time.sleep(0.5)

            code = server.get_authorisation_code()
            if not code:
                raise Exception("Did not receive authorisation code within the timeout period.")

            # Exchange the code for tokens
            tokens = self.get_tokens(code)
            refresh_token = tokens.get("refresh_token")
            access_token = tokens.get("access_token")

            if not refresh_token or not access_token:
                raise Exception("Failed to obtain refresh token.")

            # Get the username associated with this token
            username = self.get_username(access_token)

            return username, refresh_token

        finally:
            # Always stop the server
            server.stop()
