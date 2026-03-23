# activity-webhook Specification

## ADDED Requirements

### Requirement: Webhook Server Command
The system SHALL provide a `hammerhead serve` command that starts an HTTP server to receive activity notifications.

#### Scenario: Start webhook server successfully
- **WHEN** the user runs `hammerhead serve`
- **AND** `HAMMERHEAD_WEBHOOK_SECRET` is set
- **AND** `HAMMERHEAD_WEBHOOK_PORT` is valid and available
- **THEN** the system SHALL start an HTTP server on the specified port
- **AND** display "Webhook server listening on http://localhost:{port}"

#### Scenario: Start server without webhook secret
- **WHEN** the user runs `hammerhead serve`
- **AND** `HAMMERHEAD_WEBHOOK_SECRET` is not set
- **THEN** the system SHALL display an error: "HAMMERHEAD_WEBHOOK_SECRET is not set. Please configure your webhook secret."
- **AND** exit with a non-zero status code

#### Scenario: Graceful shutdown
- **WHEN** the server receives SIGINT or SIGTERM
- **THEN** the system SHALL stop accepting new requests
- **AND** complete any in-progress downloads
- **AND** exit cleanly

### Requirement: Webhook Endpoint
The system SHALL expose a POST `/webhook` endpoint that receives Hammerhead activity notifications.

#### Scenario: Receive valid webhook notification
- **WHEN** Hammerhead sends a POST to `/webhook`
- **AND** the `X-Hmac-Signature` header is valid
- **AND** the payload contains an `activityId`
- **THEN** the system SHALL respond with HTTP 200 immediately
- **AND** asynchronously download the activity FIT file
- **AND** log "Downloaded: {activity-name} ({filename}.fit)"

#### Scenario: Receive webhook with invalid signature
- **WHEN** Hammerhead sends a POST to `/webhook`
- **AND** the `X-Hmac-Signature` header is invalid or missing
- **THEN** the system SHALL respond with HTTP 401 Unauthorized
- **AND** not process the activity

### Requirement: Webhook Signature Verification
The system SHALL verify incoming webhook requests using HMAC-SHA256 signature validation.

#### Scenario: Validate correct signature
- **WHEN** a webhook POST is received
- **AND** the request body is signed with the configured secret
- **AND** the signature matches `X-Hmac-Signature`
- **THEN** the system SHALL accept the request

#### Scenario: Reject incorrect signature
- **WHEN** a webhook POST is received
- **AND** the signature does not match
- **THEN** the system SHALL reject with HTTP 401

### Requirement: Automatic Activity Download
When the webhook receives a valid activity notification, the system SHALL download the activity FIT file if it meets criteria.

#### Scenario: Download new activity
- **WHEN** a valid activity webhook is received
- **AND** the activity duration >= 5 minutes (300,000 ms)
- **AND** the activity has not been downloaded yet
- **THEN** the system SHALL download the FIT file to `HAMMERHEAD_DOWNLOADS`
- **AND** name it `{activityId}.fit`

#### Scenario: Skip short activity
- **WHEN** a valid activity webhook is received
- **AND** the activity duration < 5 minutes (300,000 ms)
- **THEN** the system SHALL skip the download
- **AND** log "Skipped: {activity-name} (duration: Xm < 5m minimum)"

#### Scenario: Skip duplicate activity
- **WHEN** a valid activity webhook is received
- **AND** a file matching `{activityId}.fit` already exists in `HAMMERHEAD_DOWNLOADS`
- **THEN** the system SHALL skip the download
- **AND** not log duplicate skips (silent)

### Requirement: Webhook Environment Configuration
The system SHALL require configuration via environment variables.

#### Scenario: Configure webhook secret
- **WHEN** the webhook server starts
- **THEN** `HAMMERHEAD_WEBHOOK_SECRET` MUST be set in `.env`
- **AND** used for HMAC signature verification

#### Scenario: Configure webhook port
- **WHEN** the webhook server starts
- **THEN** `HAMMERHEAD_WEBHOOK_PORT` MAY be set (default: 3000)
- **AND** the server listens on that port
