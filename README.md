# Hammerhead Downloader

**Download your Hammerhead activities and FIT files via a simple CLI.**

## Quick Start (under 5 minutes)

```bash
# 1) Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2) Install the CLI
pip install -e .

# 3) Configure credentials
cat > .env <<'EOF'
HAMMERHEAD_CLIENT_ID=your-client-id
HAMMERHEAD_CLIENT_SECRET=your-client-secret
HAMMERHEAD_DOWNLOADS=~/hammerhead-rides
EOF

# 4) Authorize (opens your browser)
hammerhead auth

# 5) List activities
hammerhead activities list --all
```

> [!IMPORTANT]
> Your OAuth **redirect URI must match exactly** what's configured in the Hammerhead developer portal.
> This CLI expects `http://localhost:3001/callback`, and port `3001` must be free.

## Project DNA

```
.
├── src/
│   └── hammerdownloader/
│       ├── client.py        # OAuth flow + API client
│       ├── cli.py           # CLI commands
│       └── __init__.py
├── tests/                   # Test suite
├── pyproject.toml           # Dependencies & CLI entrypoint
├── openspec/                # OpenSpec changes/specs
└── .env                     # Local credentials (you create this)
```

## Environment Specs

### Required
- **Python:** 3.11+
- **Network:** Access to `https://api.hammerhead.io`

### `.env` Requirements
Create a `.env` file in the repo root with:

```
HAMMERHEAD_CLIENT_ID=your-client-id
HAMMERHEAD_CLIENT_SECRET=your-client-secret
HAMMERHEAD_DOWNLOADS=~/hammerhead-rides
```

### Environment Variables
| Variable | Required | Description |
| --- | --- | --- |
| `HAMMERHEAD_CLIENT_ID` | Yes | OAuth client ID from Hammerhead |
| `HAMMERHEAD_CLIENT_SECRET` | Yes | OAuth client secret from Hammerhead |
| `HAMMERHEAD_DOWNLOADS` | For `--latest` | Directory to store downloaded FIT files |

### Local Files Created
- `~/.config/hammerhead-downloader/token.json` — stored OAuth tokens
- `HAMMERHEAD_DOWNLOADS/*.fit` — downloaded FIT files

## Tutorials (First Steps)

### 1) Authorize the CLI
```bash
hammerhead auth
```

### 2) List your activities
```bash
hammerhead activities list --all
```

### 3) Download a single FIT file
```bash
hammerhead activities download <activity-id>
```

### 4) Download all new activities (sync)
```bash
hammerhead activities download --latest
```

## How-to Guides (Task Solver)

### Sync all new rides
```bash
hammerhead activities download --latest
```
This downloads all activities not already in `HAMMERHEAD_DOWNLOADS`, skipping duplicates and activities under 5 minutes.

### Re-authorize a different account
```bash
hammerhead logout
hammerhead auth
```

### Check auth status
```bash
hammerhead status
```

### Use a different redirect port (if 3001 is busy)
1. Update the registered redirect URI in the Hammerhead portal.
2. Update `redirect_uri` in `src/hammerdownloader/client.py`.

## Technical Reference (Specs)

### CLI Commands

| Command | Description |
| --- | --- |
| `hammerhead auth` | Start OAuth authorization flow |
| `hammerhead status` | Check if a valid token is cached |
| `hammerhead logout` | Clear stored tokens |
| `hammerhead activities list --all` | List all activities |
| `hammerhead activities list --all --page N` | List page N |
| `hammerhead activities download <activity-id>` | Download single FIT file |
| `hammerhead activities download --latest` | Sync all new activities |

### `--latest` Flag Behavior
- Requires `HAMMERHEAD_DOWNLOADS` environment variable
- Skips activities already downloaded (by filename matching activity ID)
- Skips activities under 5 minutes duration
- Reports downloaded and skipped activities clearly

### OAuth Configuration
- **Authorization URL:** `https://api.hammerhead.io/v1/auth/oauth/authorize`
- **Token URL:** `https://api.hammerhead.io/v1/auth/oauth/token`
- **API Base URL:** `https://api.hammerhead.io/v1/api`
- **Scopes used:** `activity:read`
- **Redirect URI:** `http://localhost:3001/callback`

## Explanation (Deep Dive)

The CLI uses the **OAuth 2.0 Authorization Code** flow:

1. `hammerhead auth` opens a browser to the Hammerhead consent screen.
2. After approval, Hammerhead redirects to your local callback server.
3. The CLI exchanges the authorization code for a bearer token.
4. Tokens are stored in `~/.config/hammerhead-downloader/token.json` and refreshed automatically when possible.

---

If you change behavior or add commands, update this README in the same commit so it stays accurate.
