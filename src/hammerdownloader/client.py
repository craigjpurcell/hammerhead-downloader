"""Hammerhead API client for authentication and API calls."""

from __future__ import annotations

import json
import secrets
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests


@dataclass
class Activity:
    """Represents an activity from the Hammerhead API."""

    id: str
    name: str
    created_at: str
    started_at: str
    duration: float
    distance: float
    activity_type: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Activity:
        """Create an Activity from API response data."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            created_at=data.get("createdAt", ""),
            started_at=data.get("startedAt", ""),
            duration=data.get("duration", 0),
            distance=data.get("distance", 0),
            activity_type=data.get("activityType"),
            description=data.get("description"),
        )


@dataclass
class TokenData:
    """Stores OAuth token information."""

    access_token: str
    refresh_token: str | None
    expires_at: float
    scope: str | None

    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        return time.time() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenData:
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=data.get("expires_at", 0),
            scope=data.get("scope"),
        )


class HammerheadApiError(Exception):
    """Base exception for Hammerhead API errors."""

    pass


class AuthenticationError(HammerheadApiError):
    """Raised when authentication fails."""

    pass


class NetworkError(HammerheadApiError):
    """Raised when a network error occurs."""

    pass


class CallbackServer:
    """HTTP server to catch OAuth callback."""

    def __init__(self, port: int = 3001):
        self.port = port
        self.code: str | None = None
        self.state: str | None = None
        self.error: str | None = None
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def _create_handler(self):
        class CallbackHandler(BaseHTTPRequestHandler):
            server_instance = self

            def do_GET(self):
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)

                self.server_instance.code = query.get("code", [None])[0]
                self.server_instance.state = query.get("state", [None])[0]
                self.server_instance.error = query.get("error", [None])[0]

                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authorization Complete</h1>")
                if self.server_instance.code:
                    self.wfile.write(b"<p>You can close this window.</p>")
                elif self.server_instance.error:
                    self.wfile.write(
                        f"<p>Error: {self.server_instance.error}</p>".encode()
                    )
                self.wfile.write(b"</body></html>")

                threading.Thread(
                    target=lambda: self.server.shutdown(), daemon=True
                ).start()

            def log_message(self, format, *args):
                pass

        return CallbackHandler

    def start(self):
        """Start the callback server."""
        self._server = HTTPServer(("localhost", self.port), self._create_handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the callback server."""
        if self._server:
            self._server.shutdown()
            self._server.server_close()

    def get_callback_url(self) -> str:
        """Get the callback URL."""
        return f"http://localhost:{self.port}/callback"


class TokenStore:
    """Stores OAuth tokens securely on disk."""

    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            config_dir = Path.home() / ".config" / "hammerhead-downloader"
        self._path = config_dir / "token.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, token_data: TokenData) -> None:
        """Save token data to disk."""
        with open(self._path, "w") as f:
            json.dump(token_data.to_dict(), f)
        self._path.chmod(0o600)

    def load(self) -> TokenData | None:
        """Load token data from disk."""
        if not self._path.exists():
            return None
        try:
            with open(self._path) as f:
                return TokenData.from_dict(json.load(f))
        except (json.JSONDecodeError, KeyError):
            return None

    def clear(self) -> None:
        """Remove stored tokens."""
        if self._path.exists():
            self._path.unlink()


class HammerheadClient:
    """Client for interacting with the Hammerhead API."""

    BASE_URL = "https://api.hammerhead.io/v1/api"
    AUTH_URL = "https://api.hammerhead.io/v1/auth/oauth/authorize"
    TOKEN_URL = "https://api.hammerhead.io/v1/auth/oauth/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:3001/callback",
        scope: str = "activity:read",
        config_dir: Path | None = None,
    ) -> None:
        """Initialize the client with OAuth2 credentials."""
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._scope = scope
        self._token_store = TokenStore(config_dir)

    def _get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """Generate the authorization URL."""
        if state is None:
            state = secrets.token_urlsafe(16)

        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": self._scope,
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}", state

    def authorize(self) -> TokenData:
        """Perform the OAuth authorization flow with a local callback server."""
        callback_url, state = self._get_authorization_url()

        callback_port = int(urlparse(self._redirect_uri).port or 3001)
        server = CallbackServer(callback_port)
        server.start()

        print("Opening browser for authorization...")
        print("If browser doesn't open automatically, visit:")
        print(f"  {callback_url}")
        print()

        import webbrowser

        webbrowser.open(callback_url)

        print("Waiting for authorization...")

        while server.code is None and server.error is None:
            time.sleep(0.5)

        server.stop()

        if server.error:
            raise AuthenticationError(f"Authorization failed: {server.error}")

        if server.state != state:
            raise AuthenticationError("State mismatch - possible CSRF attack")

        if not server.code:
            raise AuthenticationError("No authorization code received")

        return self._exchange_code_for_token(server.code)

    def _exchange_code_for_token(self, code: str) -> TokenData:
        """Exchange an authorization code for access token."""
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                    "redirect_uri": self._redirect_uri,
                },
                timeout=30,
            )
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Network error: {e}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {e}")

        if response.status_code >= 400:
            raise AuthenticationError(
                f"Token exchange failed: {response.status_code} - {response.text}"
            )

        try:
            data = response.json()
        except ValueError as e:
            raise AuthenticationError(f"Invalid response: {e}")

        token_data = TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=time.time() + data.get("expires_in", 3600) - 60,
            scope=data.get("scope"),
        )
        self._token_store.save(token_data)
        return token_data

    def _refresh_token(self) -> TokenData:
        """Refresh the access token using refresh token."""
        token_data = self._token_store.load()
        if not token_data or not token_data.refresh_token:
            raise AuthenticationError(
                "No refresh token available. Please re-authorize."
            )

        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": token_data.refresh_token,
                },
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {e}")

        if response.status_code >= 400:
            self._token_store.clear()
            raise AuthenticationError("Token refresh failed. Please re-authorize.")

        data = response.json()
        new_token_data = TokenData(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", token_data.refresh_token),
            expires_at=time.time() + data.get("expires_in", 3600) - 60,
            scope=data.get("scope"),
        )
        self._token_store.save(new_token_data)
        return new_token_data

    def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        token_data = self._token_store.load()

        if token_data and not token_data.is_expired():
            return token_data.access_token

        if token_data and token_data.refresh_token:
            token_data = self._refresh_token()
            return token_data.access_token

        raise AuthenticationError(
            "Not authenticated. Run 'hammerhead auth' to authorize."
        )

    def is_authenticated(self) -> bool:
        """Check if we have a valid token."""
        token_data = self._token_store.load()
        return token_data is not None and not token_data.is_expired()

    def logout(self) -> None:
        """Clear stored tokens."""
        self._token_store.clear()

    def _make_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> requests.Response:
        """Make an authenticated request to the API."""
        try:
            token = self._get_access_token()
            headers = kwargs.pop("headers", {})
            headers["Authorization"] = f"Bearer {token}"
            response = requests.request(
                method,
                f"{self.BASE_URL}{endpoint}",
                headers=headers,
                timeout=kwargs.pop("timeout", 30),
                **kwargs,
            )
            return response
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Network error: {e}")
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Request timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {e}")

    def list_activities(
        self, page: int = 1, per_page: int = 100
    ) -> tuple[list[Activity], dict]:
        """Fetch activities from the Hammerhead API."""
        response = self._make_request(
            "GET", "/activities", params={"page": page, "perPage": per_page}
        )
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code >= 400:
            raise HammerheadApiError(f"API error: {response.status_code}")

        try:
            data = response.json()
        except ValueError as e:
            raise HammerheadApiError(f"Invalid JSON response: {e}")

        if not isinstance(data, dict) or "data" not in data:
            raise HammerheadApiError("Unexpected response format")

        activities = [Activity.from_dict(activity) for activity in data.get("data", [])]
        pagination = {
            "totalItems": data.get("totalItems", 0),
            "totalPages": data.get("totalPages", 0),
            "perPage": data.get("perPage", 0),
            "currentPage": data.get("currentPage", 0),
        }
        return activities, pagination

    def get_activity(self, activity_id: str) -> Activity:
        """Fetch a single activity by ID."""
        response = self._make_request("GET", f"/activities/{activity_id}")
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code >= 400:
            raise HammerheadApiError(f"API error: {response.status_code}")

        try:
            data = response.json()
        except ValueError as e:
            raise HammerheadApiError(f"Invalid JSON response: {e}")

        return Activity.from_dict(data)

    def get_activity_fit(self, activity_id: str) -> bytes:
        """Fetch the FIT file for an activity."""
        response = self._make_request("GET", f"/activities/{activity_id}/file")
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code >= 400:
            raise HammerheadApiError(f"API error: {response.status_code}")

        return response.content

    def get_all_activities(self) -> list[Activity]:
        """Fetch all activities from the API across all pages."""
        all_activities = []
        page = 1
        per_page = 100

        while True:
            activities, pagination = self.list_activities(page=page, per_page=per_page)
            all_activities.extend(activities)
            if page >= pagination.get("totalPages", 1):
                break
            page += 1

        return all_activities
