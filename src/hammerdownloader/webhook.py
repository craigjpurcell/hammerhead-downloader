"""Webhook server for receiving Hammerhead activity notifications."""

from __future__ import annotations

import hashlib
import hmac
import logging
import signal
import sys
import threading
from pathlib import Path
from typing import Any

from flask import Flask, Request, request, jsonify

from hammerdownloader.client import (
    HammerheadClient,
    HammerheadApiError,
    AuthenticationError,
    NetworkError,
)

MIN_DURATION_MS = 300000  # 5 minutes

logger = logging.getLogger(__name__)


def get_downloads_dir() -> Path:
    """Get the downloads directory from .env file."""
    from dotenv import load_dotenv
    from pathlib import Path
    import os

    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

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
    downloaded_ids = set()
    for fit_file in downloads_dir.glob("*.fit"):
        activity_id = fit_file.stem
        downloaded_ids.add(activity_id)
    return downloaded_ids


def verify_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    """Verify HMAC-SHA256 signature from webhook."""
    if not signature:
        return False
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


def download_activity(activity_id: str, client: HammerheadClient, downloads_dir: Path) -> str | None:
    """Download an activity if it meets criteria. Returns activity name or None if skipped."""
    try:
        activity = client.get_activity(activity_id)
    except (AuthenticationError, HammerheadApiError, NetworkError) as e:
        logger.error(f"Failed to fetch activity {activity_id}: {e}")
        return None

    if activity.duration < MIN_DURATION_MS:
        duration_m = activity.duration / 1000 / 60
        logger.info(
            f"Skipped: {activity.name} (duration: {duration_m:.1f}m < 5m minimum)"
        )
        return None

    downloaded_ids = get_downloaded_ids(downloads_dir)
    if activity.id in downloaded_ids:
        return None  # Silent skip for duplicates

    try:
        fit_data = client.get_activity_fit(activity.id)
        output_path = downloads_dir / f"{activity.id}.fit"
        
        with open(output_path, "wb") as f:
            f.write(fit_data)
        
        logger.info(f"Downloaded: {activity.name} ({output_path.name})")
        return activity.name
    except (HammerheadApiError, NetworkError, IOError) as e:
        logger.error(f"Failed to download {activity_id}: {e}")
        return None


def create_app(
    webhook_secret: str,
    client_id: str,
    client_secret: str,
) -> Flask:
    """Create Flask application for webhook server."""
    app = Flask(__name__)
    
    client = HammerheadClient(client_id, client_secret)
    downloads_dir = get_downloads_dir()
    
    @app.route("/webhook", methods=["POST"])
    def webhook() -> tuple[Any, int]:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        payload = request.get_data()
        signature = request.headers.get("X-Hmac-Signature")
        
        if not verify_signature(payload, signature, webhook_secret):
            logger.warning("Invalid webhook signature received")
            return jsonify({"error": "Invalid signature"}), 401
        
        data = request.get_json()
        activity_id = data.get("activityId")
        
        if not activity_id:
            return jsonify({"error": "Missing activityId"}), 400
        
        logger.info(f"Received webhook for activity: {activity_id}")
        
        thread = threading.Thread(
            target=download_activity,
            args=(activity_id, client, downloads_dir),
            daemon=True
        )
        thread.start()
        
        return jsonify({"status": "accepted"}), 200
    
    return app


def run_server(port: int, webhook_secret: str, client_id: str, client_secret: str) -> None:
    """Run the webhook server with graceful shutdown."""
    app = create_app(webhook_secret, client_id, client_secret)
    
    def shutdown_handler(signum: int, frame: Any) -> None:
        logger.info("Shutting down webhook server...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    logger.info(f"Webhook server listening on http://localhost:{port}")
    logger.info("Press Ctrl+C to stop")
    
    app.run(host="0.0.0.0", port=port, threaded=True)
