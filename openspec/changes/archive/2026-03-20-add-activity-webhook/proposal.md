# Proposal: add-activity-webhook

## Summary
Add a `hammerhead serve` command that starts a webhook server to receive activity notifications from the Hammerhead API, automatically downloading new activities to `HAMMERHEAD_DOWNLOADS`.

## Why
Users want automatic, real-time syncing of their ride data without manually running `hammerhead activities download --latest`. A webhook listener enables push-based downloads instead of pull-based polling.

## What Changes
- New `hammerhead serve` CLI command starts a webhook server
- Server listens on configurable port (default: 3000)
- Receives POST requests at `/webhook` endpoint
- Validates webhook signature using `X-Hmac-Signature` header
- Downloads new activity FIT files when notified
- Reuses existing download logic (duration filter, duplicate detection)

## Scope
- New `serve` subcommand in CLI
- Webhook endpoint handler with signature verification
- HMAC signature configuration via `HAMMERHEAD_WEBHOOK_SECRET`
- Server port configuration via `HAMMERHEAD_WEBHOOK_PORT`
- Graceful shutdown on SIGINT/SIGTERM

## Out of Scope
- HTTPS support (can be added via reverse proxy)
- Retry logic for failed downloads
- Multiple webhook endpoints
- Background daemonization (use systemd/supervisord externally)

## User Experience
```bash
# Add to .env
HAMMERHEAD_WEBHOOK_SECRET=your-webhook-secret
HAMMERHEAD_WEBHOOK_PORT=3000

# Start webhook server
hammerhead serve

# Server output:
Webhook server listening on http://localhost:3000
Register this URL with Hammerhead: http://your-ip:3000/webhook
Downloaded: Morning Ride (167249.activity.abc.fit)
Downloaded: Evening Ride (167249.activity.def.fit)
```
