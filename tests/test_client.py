"""Tests for the Hammerhead API client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hammerdownloader.client import (
    Activity,
    AuthenticationError,
    HammerheadClient,
    NetworkError,
)


class TestActivity:
    """Tests for the Activity dataclass."""

    def test_from_dict_with_all_fields(self) -> None:
        """Test creating an Activity from a dict with all fields."""
        data = {
            "id": "167249.activity.abc123",
            "name": "Morning Ride",
            "createdAt": "2024-01-15T08:00:00Z",
            "startedAt": "2024-01-15T08:30:00Z",
            "duration": 7200000,
            "distance": 25000,
            "activityType": "RIDE",
            "description": "Great ride!",
        }
        activity = Activity.from_dict(data)
        assert activity.id == "167249.activity.abc123"
        assert activity.name == "Morning Ride"
        assert activity.duration == 7200000
        assert activity.distance == 25000
        assert activity.activity_type == "RIDE"
        assert activity.description == "Great ride!"

    def test_from_dict_with_missing_fields(self) -> None:
        """Test creating an Activity from a dict with missing fields."""
        data: dict[str, str] = {}
        activity = Activity.from_dict(data)
        assert activity.id == ""
        assert activity.name == ""
        assert activity.duration == 0
        assert activity.distance == 0
        assert activity.activity_type is None
        assert activity.description is None


class TestListActivities:
    """Tests for the list_activities method."""

    @patch("hammerdownloader.client.HammerheadClient._make_request")
    def test_list_activities_success(self, mock_request: MagicMock) -> None:
        """Test successful activity listing."""
        mock_activities_response = MagicMock()
        mock_activities_response.status_code = 200
        mock_activities_response.json.return_value = {
            "data": [
                {
                    "id": "activity-1",
                    "name": "Morning Ride",
                    "createdAt": "2024-01-15T08:00:00Z",
                    "startedAt": "2024-01-15T08:30:00Z",
                    "duration": 7200000,
                    "distance": 25000,
                },
            ],
            "totalItems": 1,
            "totalPages": 1,
            "perPage": 10,
            "currentPage": 1,
        }
        mock_request.return_value = mock_activities_response

        client = HammerheadClient("client-id", "client-secret")
        # Mock the token fetch
        client._access_token = "test-token"
        activities, pagination = client.list_activities()

        assert len(activities) == 1
        assert activities[0].id == "activity-1"
        assert pagination["totalItems"] == 1

    @patch("hammerdownloader.client.HammerheadClient._make_request")
    def test_list_activities_auth_failure(self, mock_request: MagicMock) -> None:
        """Test activity listing with authentication failure."""
        mock_activities_response = MagicMock()
        mock_activities_response.status_code = 401
        mock_request.return_value = mock_activities_response

        client = HammerheadClient("client-id", "client-secret")
        client._access_token = "test-token"

        with pytest.raises(AuthenticationError):
            client.list_activities()
