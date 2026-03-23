# Hammerhead Downloader

**Download your Hammerhead activities and FIT files via a simple CLI.**

## Quick Start (under 5 minutes)

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
│       ├── webhook.py       # Webhook server
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
| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `HAMMERHEAD_CLIENT_ID` | Yes | - | OAuth client ID from Hammerhead |
| `HAMMERHEAD_CLIENT_SECRET` | Yes | - | OAuth client secret from Hammerhead |
| `HAMMERHEAD_DOWNLOADS` | For `--latest` / serve | - | Directory to store downloaded FIT files |
| `HAMMERHEAD_WEBHOOK_SECRET` | For `serve` | - | HMAC secret for webhook verification |
| `HAMMERHEAD_WEBHOOK_PORT` | For `serve` | 3000 | Port for webhook server |

### Local Files Created
- `~/.config/hammerhead-downloader/token.json` — stored OAuth tokens
- `HAMMERHEAD_DOWNLOADS/*.fit` — downloaded FIT files

### Pre-commit Hooks (Security)
This repository includes pre-commit hooks to prevent accidentally committing secrets:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install --hook-type pre-commit
```

The hooks will:
- Block commits containing `.env` files
- Detect AWS credentials in staged files
- Prevent direct commits to `main`

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

### 5) Start webhook server (auto-download)
```bash
# Add to .env
HAMMERHEAD_WEBHOOK_SECRET=your-webhook-secret
HAMMERHEAD_WEBHOOK_PORT=3000

# Start server
hammerhead serve
```

## How-to Guides (Task Solver)

### Sync all new rides
```bash
hammerhead activities download --latest
```
This downloads all activities not already in `HAMMERHEAD_DOWNLOADS`, skipping duplicates and activities under 5 minutes.

### Set up automatic downloads via webhook
```bash
# 1. Configure webhook secret in .env
echo "HAMMERHEAD_WEBHOOK_SECRET=your-secret" >> .env

# 2. Start the webhook server
hammerhead serve

# 3. Register your webhook URL with Hammerhead
# The server outputs the URL to register:
# Webhook server listening on http://localhost:3000
# Register this URL with Hammerhead: http://your-ip:3000/webhook
```

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
| `hammerhead serve` | Start webhook server for auto-download |
| `hammerhead serve --port 8080` | Start webhook server on specific port |

### `--latest` Flag Behavior
- Requires `HAMMERHEAD_DOWNLOADS` environment variable
- Skips activities already downloaded (by filename matching activity ID)
- Skips activities under 5 minutes duration
- Reports downloaded and skipped activities clearly

### Webhook Server Behavior
- Validates incoming requests using HMAC-SHA256 signature (`X-Hmac-Signature` header)
- Requires `HAMMERHEAD_WEBHOOK_SECRET` environment variable
- Downloads activities to `HAMMERHEAD_DOWNLOADS`
- Skips activities under 5 minutes (no logging)
- Skips duplicates silently
- Processes webhooks asynchronously

### OAuth Configuration
- **Authorization URL:** `https://api.hammerhead.io/v1/auth/oauth/authorize`
- **Token URL:** `https://api.hammerhead.io/v1/auth/oauth/token`
- **API Base URL:** `https://api.hammerhead.io/v1/api`
- **Scopes used:** `activity:read`
- **Redirect URI:** `http://localhost:3001/callback`

## Explanation (Deep Dive)

### CLI Authentication
The CLI uses the **OAuth 2.0 Authorization Code** flow:

1. `hammerhead auth` opens a browser to the Hammerhead consent screen.
2. After approval, Hammerhead redirects to your local callback server.
3. The CLI exchanges the authorization code for a bearer token.
4. Tokens are stored in `~/.config/hammerhead-downloader/token.json` and refreshed automatically when possible.

### Webhook Server
The webhook server receives push notifications from Hammerhead when new activities are recorded:

1. `hammerhead serve` starts an HTTP server on port 3000 (configurable).
2. Register your webhook URL with Hammerhead's developer portal.
3. When Hammerhead detects a new activity, it POSTs to `/webhook`.
4. The server validates the HMAC signature, then downloads the FIT file asynchronously.

---

## Contributing

### Branch Protection (GitHub Settings)

To protect the main branch, configure these settings in your GitHub repository:

**Settings → Branches → Add rule → Apply to `main`:**

| Setting | Value |
| --- | --- |
| Require pull request reviews before merging | ✓ |
| Require review from Code Owners | ✓ |
| Require status checks to pass before merging | ✓ |
| Required status checks | `test`, `Run ruff check`, `Check formatting` |
| Include administrators | ✗ |
| Allow force pushes | ✗ |
| Allow deletions | ✗ |

### CI Workflow

This repository uses GitHub Actions for continuous integration:

- Runs on all PRs and pushes to `main`
- Installs dependencies using `uv`
- Runs pytest tests
- Runs ruff linter and formatter checks

If you change behavior or add commands, update this README in the same commit so it stays accurate.
