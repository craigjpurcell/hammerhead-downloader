"""OAuth authorization flow — local callback server and URL generation."""

from __future__ import annotations

import secrets
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs


def build_authorization_url(
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str | None = None,
) -> tuple[str, str]:
    """Generate the OAuth authorization URL.

    Returns (url, state) where state is a random CSRF token.
    """
    if state is None:
        state = secrets.token_urlsafe(16)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
    }
    auth_url = "https://api.hammerhead.io/v1/auth/oauth/authorize"
    return f"{auth_url}?{urlencode(params)}", state


class CallbackServer:
    """HTTP server to catch OAuth callback."""

    def __init__(self, port: int = 3001):
        self.port = port
        self.code: str | None = None
        self.state: str | None = None
        self.error: str | None = None
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def _create_handler(self):
        class CallbackHandler(BaseHTTPRequestHandler):
            server_instance = self

            def do_GET(self):
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)

                self.server_instance.code = query.get("code", [None])[0]
                self.server_instance.state = query.get("state", [None])[0]
                self.server_instance.error = query.get("error", [None])[0]

                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Authorization Complete</h1>")
                if self.server_instance.code:
                    self.wfile.write(b"<p>You can close this window.</p>")
                elif self.server_instance.error:
                    self.wfile.write(
                        f"<p>Error: {self.server_instance.error}</p>".encode()
                    )
                self.wfile.write(b"</body></html>")

                threading.Thread(
                    target=lambda: self.server.shutdown(), daemon=True
                ).start()

            def log_message(self, format, *args):
                pass

        return CallbackHandler

    def start(self):
        """Start the callback server."""
        self._server = HTTPServer(("localhost", self.port), self._create_handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the callback server."""
        if self._server:
            self._server.shutdown()
            self._server.server_close()

    def wait_for_callback(self) -> str:
        """Block until we receive a callback code. Returns the code."""
        while self.code is None and self.error is None:
            time.sleep(0.5)
        return self.code  # caller checks error/state
