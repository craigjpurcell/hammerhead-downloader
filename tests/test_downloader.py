"""Tests for the download orchestrator."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from hammerdownloader.downloader import (
    download_new_activities,
    get_downloaded_ids,
    get_downloads_dir,
    MIN_DURATION_MS,
)
from hammerdownloader.models import Activity


class TestGetDownloadsDir:
    """Tests for the get_downloads_dir function."""

    def test_get_downloads_dir_set(self) -> None:
        """Test when HAMMERHEAD_DOWNLOADS is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HAMMERHEAD_DOWNLOADS": tmpdir}):
                result = get_downloads_dir()
                assert result.resolve() == Path(tmpdir).resolve()


class TestGetDownloadedIds:
    """Tests for the get_downloaded_ids function."""

    def test_get_downloaded_ids_empty_dir(self) -> None:
        """Test when directory has no FIT files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ids = get_downloaded_ids(Path(tmpdir))
            assert ids == set()

    def test_get_downloaded_ids_with_files(self) -> None:
        """Test extracting IDs from FIT filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "167249.activity.abc123.fit").touch()
            (tmppath / "167249.activity.def456.fit").touch()
            (tmppath / "other-file.txt").touch()

            ids = get_downloaded_ids(tmppath)
            assert ids == {"167249.activity.abc123", "167249.activity.def456"}


class TestMinDurationFilter:
    """Tests for the minimum duration filter."""

    def test_min_duration_constant(self) -> None:
        """Test that MIN_DURATION_MS is correctly set to 5 minutes."""
        assert MIN_DURATION_MS == 300000


class TestDownloadNewActivities:
    """Tests for the download_new_activities function."""

    @patch("hammerdownloader.downloader.print")
    def test_no_new_activities(self, mock_print: MagicMock) -> None:
        """Test when no activities exist at all."""
        client = MagicMock()
        client.get_all_activities.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            download_new_activities(client, Path(tmpdir))

        mock_print.assert_called_with("No new activities to download.")

    @patch("hammerdownloader.downloader.print")
    def test_skips_existing_activities(self, mock_print: MagicMock) -> None:
        """Test activities already downloaded are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a pre-existing FIT file
            (Path(tmpdir) / "existing.activity.123.fit").write_bytes(b"EXISTING")

            client = MagicMock()
            client.get_all_activities.return_value = [
                Activity(
                    id="existing.activity.123",
                    name="Morning Ride",
                    created_at="2024-01-15T08:00:00Z",
                    started_at="2024-01-15T08:30:00Z",
                    duration=7200000,
                    distance=25000,
                )
            ]
            client.get_activity_fit.return_value = b"FIT_DATA"

            download_new_activities(client, Path(tmpdir))

            client.get_activity_fit.assert_not_called()
            mock_print.assert_called_with("No new activities to download.")

    @patch("hammerdownloader.downloader.print")
    def test_skips_short_activities(self, mock_print: MagicMock) -> None:
        """Test activities under 5 minutes are skipped."""
        client = MagicMock()
        client.get_all_activities.return_value = [
            Activity(
                id="short.activity.456",
                name="Short Spin",
                created_at="2024-01-15T08:00:00Z",
                started_at="2024-01-15T08:00:00Z",
                duration=240000,  # 4 minutes
                distance=5000,
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            download_new_activities(client, Path(tmpdir))

        client.get_activity_fit.assert_not_called()
        mock_print.assert_any_call(
            "X Skipped: Short Spin (duration: 4.0m < 5m minimum)"
        )

    @patch("hammerdownloader.downloader.print")
    def test_downloads_new_activity(self, mock_print: MagicMock) -> None:
        """Test a new eligible activity is downloaded."""
        client = MagicMock()
        client.get_all_activities.return_value = [
            Activity(
                id="new.activity.789",
                name="Long Ride",
                created_at="2024-01-15T08:00:00Z",
                started_at="2024-01-15T09:00:00Z",
                duration=10800000,  # 180 minutes
                distance=50000,
            )
        ]
        client.get_activity_fit.return_value = b"FIT_FILE_DATA"

        with tempfile.TemporaryDirectory() as tmpdir:
            download_new_activities(client, Path(tmpdir))

            client.get_activity_fit.assert_called_once_with("new.activity.789")
            output_path = Path(tmpdir) / "new.activity.789.fit"
            assert output_path.exists()
            assert output_path.read_bytes() == b"FIT_FILE_DATA"

        mock_print.assert_any_call("Downloading 1 new activities...")
