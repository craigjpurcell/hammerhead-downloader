# Tasks: add-activity-webhook

## Implementation Order

### Phase 1: Webhook Server Core
1. [x] **Add webhook handler module** `src/hammerdownloader/webhook.py`
   - Flask app with `/webhook` POST endpoint
   - HMAC signature verification using `HAMMERHEAD_WEBHOOK_SECRET`
   - Return 200 immediately, process async
   - Return 401 for invalid signatures

2. [x] **Add `serve` CLI command** in `cli.py`
   - `@cli.command("serve")`
   - Parse `--port` option (default from env or 3000)
   - Load required env vars (`HAMMERHEAD_WEBHOOK_SECRET`)
   - Start webhook server
   - Handle SIGINT/SIGTERM for graceful shutdown

3. [x] **Add webhook download logic**
   - Use existing `HammerheadClient.get_activity()` to fetch activity details
   - Check duration >= 5 minutes
   - Check not already downloaded
   - Download FIT file using existing client
   - Log download result

### Phase 2: Configuration
4. [x] **Add webhook environment variables**
   - `HAMMERHEAD_WEBHOOK_SECRET` - Required HMAC secret
   - `HAMMERHEAD_WEBHOOK_PORT` - Port to listen on (default: 3000)

### Phase 3: Output & Logging
5. [x] **Add server output formatting**
   - Show startup message with URL
   - Log incoming webhook notifications
   - Log download success/failure
   - Show when activity skipped (duration/duplicate)

### Phase 4: Testing
6. [x] **Add webhook signature verification tests**
   - Valid signature passes
   - Invalid signature returns 401

7. [x] **Add webhook handler tests**
   - Mock activity fetch and download
   - Test duration filter integration
   - Test duplicate detection integration

### Phase 5: Documentation
8. [x] **Update README.md**
   - Document `hammerhead serve` command
   - Document webhook environment variables
   - Add webhook setup instructions
