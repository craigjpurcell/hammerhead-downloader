"""Tests for the webhook server."""

from __future__ import annotations

import hashlib
import hmac
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hammerdownloader.webhook import verify_signature, download_activity, MIN_DURATION_MS
from hammerdownloader.client import Activity


class TestVerifySignature:
    """Tests for webhook signature verification."""

    def test_verify_valid_signature(self) -> None:
        """Test that valid HMAC signature passes."""
        payload = b'{"activityId": "test-123"}'
        secret = "my-secret"
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        
        assert verify_signature(payload, signature, secret) is True

    def test_verify_invalid_signature(self) -> None:
        """Test that invalid signature fails."""
        payload = b'{"activityId": "test-123"}'
        secret = "my-secret"
        
        assert verify_signature(payload, "invalid", secret) is False

    def test_verify_missing_signature(self) -> None:
        """Test that missing signature fails."""
        payload = b'{"activityId": "test-123"}'
        secret = "my-secret"
        
        assert verify_signature(payload, None, secret) is False

    def test_verify_empty_signature(self) -> None:
        """Test that empty signature fails."""
        payload = b'{"activityId": "test-123"}'
        secret = "my-secret"
        
        assert verify_signature(payload, "", secret) is False


class TestDownloadActivity:
    """Tests for activity download logic."""

    @patch("hammerdownloader.webhook.HammerheadClient")
    def test_download_long_activity(self, mock_client_class: MagicMock) -> None:
        """Test downloading activity >= 5 minutes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = MagicMock()
            mock_client.get_activity.return_value = Activity(
                id="test.activity.123",
                name="Morning Ride",
                created_at="2024-01-15T08:00:00Z",
                started_at="2024-01-15T08:30:00Z",
                duration=7200000,  # 120 minutes
                distance=25000,
            )
            mock_client.get_activity_fit.return_value = b"FIT_FILE_DATA"
            mock_client_class.return_value = mock_client
            
            result = download_activity(
                "test.activity.123",
                mock_client,
                Path(tmpdir)
            )
            
            assert result == "Morning Ride"
            assert (Path(tmpdir) / "test.activity.123.fit").exists()

    @patch("hammerdownloader.webhook.HammerheadClient")
    def test_skip_short_activity(self, mock_client_class: MagicMock) -> None:
        """Test skipping activity < 5 minutes."""
        mock_client = MagicMock()
        mock_client.get_activity.return_value = Activity(
            id="test.activity.123",
            name="Short Spin",
            created_at="2024-01-15T08:00:00Z",
            started_at="2024-01-15T08:00:00Z",
            duration=180000,  # 3 minutes - too short
            distance=2000,
        )
        mock_client_class.return_value = mock_client
        
        result = download_activity(
            "test.activity.123",
            mock_client,
            Path(tempfile.gettempdir())
        )
        
        assert result is None
        mock_client.get_activity_fit.assert_not_called()

    @patch("hammerdownloader.webhook.HammerheadClient")
    def test_skip_duplicate_activity(self, mock_client_class: MagicMock) -> None:
        """Test skipping already-downloaded activity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing file
            (Path(tmpdir) / "test.activity.123.fit").write_bytes(b"EXISTING")
            
            mock_client = MagicMock()
            mock_client.get_activity.return_value = Activity(
                id="test.activity.123",
                name="Morning Ride",
                created_at="2024-01-15T08:00:00Z",
                started_at="2024-01-15T08:30:00Z",
                duration=7200000,
                distance=25000,
            )
            mock_client_class.return_value = mock_client
            
            result = download_activity(
                "test.activity.123",
                mock_client,
                Path(tmpdir)
            )
            
            assert result is None
            mock_client.get_activity_fit.assert_not_called()


class TestMinDurationFilter:
    """Tests for the minimum duration filter."""

    def test_min_duration_constant(self) -> None:
        """Test that MIN_DURATION_MS is correctly set to 5 minutes."""
        assert MIN_DURATION_MS == 300000
