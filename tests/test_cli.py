"""Tests for the CLI."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from hammerdownloader.cli import cli


class TestCli:
    """Tests for the CLI commands."""

    def test_cli_without_args(self) -> None:
        """Test CLI runs without arguments (shows help)."""
        runner = CliRunner()
        result = runner.invoke(cli)
        assert result.exit_code in (0, 2)

    @patch("hammerdownloader.cli.get_downloads_dir")
    def test_download_missing_downloads_dir(
        self, mock_get_downloads_dir: MagicMock
    ) -> None:
        """Test download when HAMMERHEAD_DOWNLOADS is not set."""
        mock_get_downloads_dir.side_effect = ValueError(
            "HAMMERHEAD_DOWNLOADS is not set. Please set it in your .env file."
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["download"])
        assert result.exit_code != 0
        assert "HAMMERHEAD_DOWNLOADS" in result.output

    @patch("hammerdownloader.cli.get_client")
    @patch("hammerdownloader.cli.get_downloads_dir")
    def test_download_no_new_activities(
        self, mock_dir: MagicMock, mock_get_client: MagicMock
    ) -> None:
        """Test download when no new activities exist."""
        mock_dir.return_value = Path(tempfile.gettempdir())

        mock_client = MagicMock()
        mock_client.get_all_activities.return_value = []
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["download"])
        assert result.exit_code == 0
        assert "No new activities to download" in result.output
