"""Hammerhead API client for authenticated HTTP calls."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from hammerdownloader.auth import CallbackServer, build_authorization_url
from hammerdownloader.models import (
    Activity,
    AuthenticationError,
    HammerheadApiError,
    NetworkError,
    TokenData,
)
from hammerdownloader.store import TokenStore


class HammerheadClient:
    """Client for interacting with the Hammerhead API."""

    BASE_URL = "https://api.hammerhead.io/v1/api"
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

    def authorize(self) -> TokenData:
        """Perform the OAuth authorization flow with a local callback server."""
        callback_url, state = build_authorization_url(
            self._client_id, self._redirect_uri, self._scope
        )

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

        server.wait_for_callback()
        server.stop()

        if server.error:
            raise AuthenticationError(f"Authorization failed: {server.error}")

        if server.state != state:
            raise AuthenticationError("State mismatch — possible CSRF attack")

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
                f"Token exchange failed: {response.status_code} — {response.text}"
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

        activities = [Activity.from_dict(item) for item in data.get("data", [])]
        pagination = {
            "totalItems": data.get("totalItems", 0),
            "totalPages": data.get("totalPages", 0),
            "perPage": data.get("perPage", 0),
            "currentPage": data.get("currentPage", 0),
        }
        return activities, pagination

    def get_all_activities(self) -> list[Activity]:
        """Fetch all activities from the API across all pages."""
        all_activities: list[Activity] = []
        page = 1
        per_page = 100

        while True:
            activities, pagination = self.list_activities(page=page, per_page=per_page)
            all_activities.extend(activities)
            if page >= pagination.get("totalPages", 1):
                break
            page += 1

        return all_activities

    def get_activity_fit(self, activity_id: str) -> bytes:
        """Fetch the FIT file for an activity."""
        response = self._make_request("GET", f"/activities/{activity_id}/file")
        if response.status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif response.status_code >= 400:
            raise HammerheadApiError(f"API error: {response.status_code}")

        return response.content
