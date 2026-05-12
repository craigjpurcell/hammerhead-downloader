# Hammerhead Downloader

**Download your Hammerhead ride data as FIT files — simply and repeatedly.**

## Quick Start

```bash
# 1) Create & activate a virtual environment
uv venv
source .venv/bin/activate

# 2) Install the CLI
uv pip install -e .

# 3) Configure credentials
cat > .env <<'EOF'
HAMMERHEAD_CLIENT_ID=your-client-id
HAMMERHEAD_CLIENT_SECRET=your-client-secret
HAMMERHEAD_DOWNLOADS=~/hammerhead-rides
EOF

# 4) Authorize (opens your browser)
hammerhead auth

# 5) Download all new activities
hammerhead download
```

> [!IMPORTANT]
> Your OAuth **redirect URI must match exactly** what's configured in the Hammerhead developer portal.
> This CLI expects `http://localhost:3001/callback`, and port `3001` must be free.

## Usage

```
hammerhead auth          # one-time OAuth authorization
hammerhead download      # download new activities to HAMMERHEAD_DOWNLOADS
```

### `hammerhead download` behavior
- Downloads all activities not already present in `HAMMERHEAD_DOWNLOADS`
- Skips activities already downloaded (identified by filename matching activity ID)
- Skips activities under 5 minutes duration
- Reports downloaded and skipped activities clearly

## Project Structure

```
.
├── src/
│   └── hammerdownloader/
│       ├── __init__.py
│       ├── cli.py           # CLI commands (thin)
│       ├── client.py        # HTTP API client
│       ├── auth.py          # OAuth callback server & URL generation
│       ├── store.py         # OAuth token persistence
│       ├── models.py        # Data classes & exceptions
│       └── downloader.py    # Download orchestration
├── tests/                   # Test suite
├── pyproject.toml           # Dependencies & CLI entrypoint
└── .env                     # Local credentials (you create this)
```

## Configuration

### `.env` file

```
HAMMERHEAD_CLIENT_ID=your-client-id
HAMMERHEAD_CLIENT_SECRET=your-client-secret
HAMMERHEAD_DOWNLOADS=~/hammerhead-rides
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `HAMMERHEAD_CLIENT_ID` | Yes | — | OAuth client ID from Hammerhead |
| `HAMMERHEAD_CLIENT_SECRET` | Yes | — | OAuth client secret from Hammerhead |
| `HAMMERHEAD_DOWNLOADS` | Yes | — | Directory to store downloaded FIT files |

### Local files created
- `~/.config/hammerhead-downloader/token.json` — stored OAuth tokens
- `HAMMERHEAD_DOWNLOADS/*.fit` — downloaded FIT files

## OAuth Configuration
- **Authorization URL:** `https://api.hammerhead.io/v1/auth/oauth/authorize`
- **Token URL:** `https://api.hammerhead.io/v1/auth/oauth/token`
- **API Base URL:** `https://api.hammerhead.io/v1/api`
- **Scopes used:** `activity:read`
- **Redirect URI:** `http://localhost:3001/callback`

The CLI uses the **OAuth 2.0 Authorization Code** flow:

1. `hammerhead auth` opens a browser to the Hammerhead consent screen.
2. After approval, Hammerhead redirects to your local callback server.
3. The CLI exchanges the authorization code for a bearer token.
4. Tokens are stored in `~/.config/hammerhead-downloader/token.json` and refreshed automatically when possible.

## Contributing

### Pre-commit Hooks (Security)
```bash
uv tool install pre-commit
pre-commit install
```
Blocks commits containing `.env` files and prevents direct commits to `main`.

### CI Workflow
GitHub Actions runs on all PRs and pushes to `main`:
- Installs dependencies using `uv`
- Runs pytest tests
- Runs ruff linter and formatter checks

If you change behavior or add commands, update this README in the same commit.
