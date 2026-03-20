"""CLI for Hammerhead Downloader."""

from __future__ import annotations

import os
from pathlib import Path

import click
from dotenv import load_dotenv

from hammerdownloader.client import (
    Activity,
    AuthenticationError,
    HammerheadApiError,
    HammerheadClient,
    NetworkError,
)

MIN_DURATION_MS = 300000  # 5 minutes


def _load_env() -> None:
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)


def load_credentials() -> tuple[str, str]:
    """Load credentials from .env file."""
    _load_env()

    client_id = os.environ.get("HAMMERHEAD_CLIENT_ID")
    client_secret = os.environ.get("HAMMERHEAD_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise click.ClickException(
            "Missing credentials. Set HAMMERHEAD_CLIENT_ID and "
            "HAMMERHEAD_CLIENT_SECRET in .env file"
        )

    return client_id, client_secret


def get_client() -> HammerheadClient:
    """Create a Hammerhead client with credentials from .env."""
    client_id, client_secret = load_credentials()
    return HammerheadClient(client_id, client_secret)


def get_downloads_dir() -> Path:
    """Get the downloads directory from .env file."""
    _load_env()

    downloads_path = os.environ.get("HAMMERHEAD_DOWNLOADS")
    if not downloads_path:
        raise click.ClickException(
            "HAMMERHEAD_DOWNLOADS is not set. Please set it in your .env file."
        )
    path = Path(downloads_path).expanduser().resolve()
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_downloaded_ids(downloads_dir: Path) -> set[str]:
    """Scan downloads directory for existing FIT files and extract activity IDs."""
    downloaded_ids = set()
    for fit_file in downloads_dir.glob("*.fit"):
        activity_id = fit_file.stem
        downloaded_ids.add(activity_id)
    return downloaded_ids


def format_activities_table(
    activities: list[Activity], pagination: dict | None = None
) -> str:
    """Format activities as a table."""
    if not activities:
        return "No activities found."

    header = f"{'ID':<45} {'Name':<25} {'Duration':<12} {'Distance':<12}"
    separator = "-" * 94
    rows = []
    for activity in activities:
        duration_str = (
            f"{activity.duration / 1000 / 60:.1f}m" if activity.duration else "0m"
        )
        distance_str = (
            f"{activity.distance / 1000:.1f}km" if activity.distance else "0km"
        )
        rows.append(
            f"{activity.id:<45} {activity.name:<25} {duration_str:<12} {distance_str:<12}"
        )

    result = "\n".join([header, separator] + rows)
    if pagination:
        result += f"\n\nPage {pagination['currentPage']} of {pagination['totalPages']} ({pagination['totalItems']} total)"
    return result


@click.group()
def cli() -> None:
    """Hammerhead Downloader - Download activity data from Hammerhead API."""
    pass


@cli.command()
def auth() -> None:
    """Authorize the application with your Hammerhead account."""
    try:
        client = get_client()

        if client.is_authenticated():
            click.echo("Already authenticated.")
            if click.confirm("Re-authorize?"):
                client.logout()
            else:
                return

        click.echo("Starting authorization flow...")
        click.echo()
        token_data = client.authorize()
        click.echo()
        click.echo("Successfully authenticated!")
        click.echo(
            f"Token expires in: {int(token_data.expires_at - __import__('time').time())} seconds"
        )
    except AuthenticationError as e:
        raise click.ClickException(f"Authentication failed: {e}")
    except NetworkError as e:
        raise click.ClickException(f"Network error: {e}")


@cli.command()
def status() -> None:
    """Check authentication status."""
    try:
        client = get_client()

        if client.is_authenticated():
            click.echo("Status: Authenticated")
        else:
            click.echo("Status: Not authenticated")
            click.echo("Run 'hammerhead auth' to authorize.")
    except Exception as e:
        raise click.ClickException(f"Error: {e}")


@cli.command()
def logout() -> None:
    """Log out and clear stored credentials."""
    try:
        client = get_client()
        client.logout()
        click.echo("Logged out successfully.")
    except Exception as e:
        raise click.ClickException(f"Error: {e}")


@cli.group()
def activities() -> None:
    """Manage activities."""
    pass


@activities.command("list")
@click.option("--all", "list_all", is_flag=True, help="List all activities")
@click.option("--page", default=1, help="Page number")
def list_activities(list_all: bool, page: int) -> None:
    """List your activities."""
    if not list_all:
        click.echo("Use 'hammerhead activities list --all' to list all activities")
        return

    try:
        client = get_client()
        activities_list, pagination = client.list_activities(page=page, per_page=100)
        click.echo(format_activities_table(activities_list, pagination))
    except AuthenticationError as e:
        raise click.ClickException(
            f"Authentication failed: {e}\nRun 'hammerhead auth' to authorize."
        )
    except NetworkError as e:
        raise click.ClickException(f"Network error: {e}")
    except HammerheadApiError as e:
        raise click.ClickException(f"API error: {e}")


@activities.command("download")
@click.argument("activity_id", required=False)
@click.option("--output", "-o", default=None, help="Output file path")
@click.option(
    "--latest",
    "download_latest",
    is_flag=True,
    help="Download all new activities to HAMMERHEAD_DOWNLOADS",
)
def download_activity(
    activity_id: str | None, output: str | None, download_latest: bool
) -> None:
    """Download FIT file(s) for activity(ies)."""
    try:
        downloads_dir = get_downloads_dir()
    except click.ClickException:
        if not download_latest:
            raise
        downloads_dir = None

    try:
        if download_latest:
            _download_latest(downloads_dir)
        elif activity_id:
            _download_single(activity_id, output)
        else:
            raise click.ClickException(
                "Specify an activity ID or use --latest to download all new activities."
            )
    except AuthenticationError as e:
        raise click.ClickException(
            f"Authentication failed: {e}\nRun 'hammerhead auth' to authorize."
        )
    except NetworkError as e:
        raise click.ClickException(f"Network error: {e}")
    except HammerheadApiError as e:
        raise click.ClickException(f"API error: {e}")
    except IOError as e:
        raise click.ClickException(f"File error: {e}")


def _download_single(activity_id: str, output: str | None) -> None:
    """Download a single activity by ID."""
    client = get_client()
    fit_data = client.get_activity_fit(activity_id)

    if output is None:
        output = f"{activity_id}.fit"

    with open(output, "wb") as f:
        f.write(fit_data)

    click.echo(f"Downloaded {len(fit_data)} bytes to {output}")


def _download_latest(downloads_dir: Path | None) -> None:
    """Download all new activities not yet downloaded."""
    if downloads_dir is None:
        downloads_dir = get_downloads_dir()

    client = get_client()
    downloaded_ids = get_downloaded_ids(downloads_dir)
    all_activities = client.get_all_activities()

    to_download = []
    skipped_short = []

    for activity in all_activities:
        if activity.id in downloaded_ids:
            continue
        if activity.duration < MIN_DURATION_MS:
            duration_m = activity.duration / 1000 / 60
            skipped_short.append((activity, duration_m))
            continue
        to_download.append(activity)

    if not to_download:
        if skipped_short:
            for activity, _ in skipped_short:
                duration_m = activity.duration / 1000 / 60
                click.echo(
                    f"X Skipped: {activity.name} (duration: {duration_m:.1f}m < 5m minimum)"
                )
            click.echo("No new activities to download.")
        else:
            click.echo("No new activities to download.")
        return

    click.echo(f"Downloading {len(to_download)} new activities...")

    downloaded_count = 0
    for activity in to_download:
        fit_data = client.get_activity_fit(activity.id)
        output_path = downloads_dir / f"{activity.id}.fit"

        with open(output_path, "wb") as f:
            f.write(fit_data)

        distance_km = activity.distance / 1000
        duration_m = activity.duration / 1000 / 60
        click.echo(
            f"  [+] {activity.name} ({output_path.name}) - "
            f"{distance_km:.1f}km, {duration_m:.1f}m"
        )
        downloaded_count += 1

    for activity, duration_m in skipped_short:
        click.echo(
            f"  [-] Skipped: {activity.name} (duration: {duration_m:.1f}m < 5m minimum)"
        )

    click.echo(f"Downloaded {downloaded_count} FIT files to {downloads_dir}")


if __name__ == "__main__":
    cli()
