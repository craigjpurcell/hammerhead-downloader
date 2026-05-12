"""Tests for data models."""

from __future__ import annotations

from hammerdownloader.models import Activity


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
