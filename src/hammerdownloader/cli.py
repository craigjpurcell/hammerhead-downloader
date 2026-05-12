"""CLI for Hammerhead Downloader."""

from __future__ import annotations

import os
from pathlib import Path

import click
from dotenv import load_dotenv

from hammerdownloader.client import HammerheadClient
from hammerdownloader.downloader import (
    download_new_activities,
    get_downloads_dir,
)
from hammerdownloader.models import AuthenticationError, NetworkError


def _load_env() -> None:
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)


def get_client() -> HammerheadClient:
    """Create a Hammerhead client with credentials from environment."""
    client_id = os.environ.get("HAMMERHEAD_CLIENT_ID")
    client_secret = os.environ.get("HAMMERHEAD_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise click.ClickException(
            "Missing credentials. Set HAMMERHEAD_CLIENT_ID and "
            "HAMMERHEAD_CLIENT_SECRET in .env file"
        )

    return HammerheadClient(client_id, client_secret)


@click.group()
def cli() -> None:
    """Hammerhead Downloader — download ride data from Hammerhead API."""


@cli.command()
def auth() -> None:
    """Authorize the application with your Hammerhead account."""
    try:
        _load_env()
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
def download() -> None:
    """Download all new activities to HAMMERHEAD_DOWNLOADS."""
    _load_env()

    try:
        downloads_dir = get_downloads_dir()
    except ValueError as e:
        raise click.ClickException(str(e))

    try:
        client = get_client()
        download_new_activities(client, downloads_dir)
    except AuthenticationError as e:
        raise click.ClickException(
            f"Authentication failed: {e}\nRun 'hammerhead auth' to authorize."
        )
    except NetworkError as e:
        raise click.ClickException(f"Network error: {e}")
    except Exception as e:
        raise click.ClickException(f"Error: {e}")


if __name__ == "__main__":
    cli()
