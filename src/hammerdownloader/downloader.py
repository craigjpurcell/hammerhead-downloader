"""Download orchestration — scan, filter, and download new activities."""

from __future__ import annotations

import os
from pathlib import Path

from hammerdownloader.client import HammerheadClient
from hammerdownloader.models import Activity

MIN_DURATION_MS = 300000  # 5 minutes


def get_downloads_dir() -> Path:
    """Get the downloads directory from environment."""
    downloads_path = os.environ.get("HAMMERHEAD_DOWNLOADS")
    if not downloads_path:
        raise ValueError(
            "HAMMERHEAD_DOWNLOADS is not set. Please set it in your .env file."
        )
    path = Path(downloads_path).expanduser().resolve()
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_downloaded_ids(downloads_dir: Path) -> set[str]:
    """Scan downloads directory for existing FIT files and extract activity IDs."""
    downloaded_ids: set[str] = set()
    for fit_file in downloads_dir.glob("*.fit"):
        downloaded_ids.add(fit_file.stem)
    return downloaded_ids


def download_new_activities(client: HammerheadClient, downloads_dir: Path) -> None:
    """Download all new activities not yet downloaded, skipping short ones."""
    downloaded_ids = get_downloaded_ids(downloads_dir)
    all_activities = client.get_all_activities()

    to_download: list[Activity] = []
    skipped_short: list[tuple[Activity, float]] = []

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
            for activity, duration_m in skipped_short:
                print(
                    f"X Skipped: {activity.name} (duration: {duration_m:.1f}m < 5m minimum)"
                )
            print("No new activities to download.")
        else:
            print("No new activities to download.")
        return

    print(f"Downloading {len(to_download)} new activities...")

    downloaded_count = 0
    for activity in to_download:
        fit_data = client.get_activity_fit(activity.id)
        output_path = downloads_dir / f"{activity.id}.fit"

        with open(output_path, "wb") as f:
            f.write(fit_data)

        distance_km = activity.distance / 1000
        duration_m = activity.duration / 1000 / 60
        print(
            f"  [+] {activity.name} ({output_path.name}) — "
            f"{distance_km:.1f}km, {duration_m:.1f}m"
        )
        downloaded_count += 1

    for activity, duration_m in skipped_short:
        print(
            f"  [-] Skipped: {activity.name} (duration: {duration_m:.1f}m < 5m minimum)"
        )

    print(f"Downloaded {downloaded_count} FIT files to {downloads_dir}")
