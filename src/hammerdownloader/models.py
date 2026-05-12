"""Data models for the Hammerhead Downloader."""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Any


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


class AuthenticationError(HammerheadApiError):
    """Raised when authentication fails."""


class NetworkError(HammerheadApiError):
    """Raised when a network error occurs."""
