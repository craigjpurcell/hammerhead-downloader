"""Tests for the CLI."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from hammerdownloader.cli import (
    cli,
    format_activities_table,
    get_downloaded_ids,
    get_downloads_dir,
    MIN_DURATION_MS,
)
from hammerdownloader.client import Activity


class TestGetDownloadsDir:
    """Tests for the get_downloads_dir function."""

    def test_get_downloads_dir_missing(self) -> None:
        """Test error when HAMMERHEAD_DOWNLOADS is not set."""
        import os as os_module
        # Create empty .env
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("")
            env_file = f.name
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                with patch('hammerdownloader.cli.load_dotenv'):
                    runner = CliRunner()
                    result = runner.invoke(cli, ["activities", "download", "--latest"])
                    assert result.exit_code != 0
                    assert "HAMMERHEAD_DOWNLOADS" in result.output
        finally:
            os_module.unlink(env_file)

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


class TestFormatActivitiesTable:
    """Tests for the format_activities_table function."""

    def test_format_activities_table_empty(self) -> None:
        """Test formatting with no activities."""
        result = format_activities_table([])
        assert result == "No activities found."

    def test_format_activities_table_with_activities(self) -> None:
        """Test formatting with activities."""
        activities = [
            Activity(
                id="167249.activity.abc123",
                name="Morning Ride",
                created_at="2024-01-15T08:00:00Z",
                started_at="2024-01-15T08:30:00Z",
                duration=7200000,
                distance=25000,
            )
        ]
        result = format_activities_table(activities)
        assert "167249.activity.abc123" in result
        assert "Morning Ride" in result
        assert "120.0m" in result
        assert "25.0km" in result


class TestCli:
    """Tests for the CLI commands."""

    def test_cli_without_flag(self) -> None:
        """Test CLI runs without flags."""
        runner = CliRunner()
        result = runner.invoke(cli)
        assert result.exit_code in (0, 2)

    def test_activities_command_without_all_flag(self) -> None:
        """Test activities command without --all flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["activities", "list"])
        assert "Use 'hammerhead activities list --all' to list all activities" in result.output

    @patch("hammerdownloader.cli.load_credentials")
    def test_activities_command_missing_credentials(self, mock_load: MagicMock) -> None:
        """Test activities command with missing credentials."""
        import click

        mock_load.side_effect = click.ClickException(
            "Missing credentials. Set HAMMERHEAD_CLIENT_ID and "
            "HAMMERHEAD_CLIENT_SECRET in .env file"
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["activities", "list", "--all"])
        assert result.exit_code != 0
        assert "Missing credentials" in result.output


class TestDownloadCommand:
    """Tests for the download command."""

    def test_download_without_args_or_flag(self) -> None:
        """Test download without activity_id or --latest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"HAMMERHEAD_DOWNLOADS": tmpdir}):
                runner = CliRunner()
                result = runner.invoke(cli, ["activities", "download"])
                assert result.exit_code != 0
                assert "Specify an activity ID" in result.output

    @patch("hammerdownloader.cli.get_client")
    @patch("hammerdownloader.cli.get_downloads_dir")
    def test_download_latest_no_new_activities(
        self, mock_dir: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test --latest when no new activities exist."""
        mock_dir.return_value = Path(tempfile.gettempdir())

        mock_client_instance = MagicMock()
        mock_client_instance.get_all_activities.return_value = []
        mock_client.return_value = mock_client_instance

        runner = CliRunner()
        result = runner.invoke(cli, ["activities", "download", "--latest"])
        assert result.exit_code == 0
        assert "No new activities to download" in result.output

    @patch("hammerdownloader.cli.get_client")
    @patch("hammerdownloader.cli.get_downloads_dir")
    def test_download_latest_skips_short_activities(
        self, mock_dir: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test that activities < 5 min are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_dir.return_value = Path(tmpdir)

            mock_client_instance = MagicMock()
            mock_client_instance.get_all_activities.return_value = [
                Activity(
                    id="short.activity",
                    name="Short Spin",
                    created_at="2024-01-15T08:00:00Z",
                    started_at="2024-01-15T08:00:00Z",
                    duration=240000,  # 4 minutes
                    distance=5000,
                )
            ]
            mock_client.return_value = mock_client_instance

            runner = CliRunner()
            result = runner.invoke(cli, ["activities", "download", "--latest"])
            assert result.exit_code == 0
            assert "Skipped" in result.output
            assert "4.0m < 5m minimum" in result.output
            assert "No new activities to download" in result.output


class TestMinDurationFilter:
    """Tests for the minimum duration filter."""

    def test_min_duration_constant(self) -> None:
        """Test that MIN_DURATION_MS is correctly set to 5 minutes."""
        assert MIN_DURATION_MS == 300000
