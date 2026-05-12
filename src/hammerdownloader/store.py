"""OAuth token persistence."""

from __future__ import annotations

import json
from pathlib import Path

from hammerdownloader.models import TokenData


class TokenStore:
    """Stores OAuth tokens securely on disk."""

    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            config_dir = Path.home() / ".config" / "hammerhead-downloader"
        self._path = config_dir / "token.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, token_data: TokenData) -> None:
        """Save token data to disk."""
        with open(self._path, "w") as f:
            json.dump(token_data.to_dict(), f)
        self._path.chmod(0o600)

    def load(self) -> TokenData | None:
        """Load token data from disk."""
        if not self._path.exists():
            return None
        try:
            with open(self._path) as f:
                return TokenData.from_dict(json.load(f))
        except (json.JSONDecodeError, KeyError):
            return None

    def clear(self) -> None:
        """Remove stored tokens."""
        if self._path.exists():
            self._path.unlink()
