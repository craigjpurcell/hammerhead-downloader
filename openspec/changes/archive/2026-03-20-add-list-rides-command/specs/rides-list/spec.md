## ADDED Requirements

### Requirement: Rides List Command
The system SHALL provide a command-line option `--all` that lists all rides from the Hammerhead API with their unique identifiers.

#### Scenario: List all rides successfully
- **WHEN** the user runs the CLI with `--all` flag
- **AND** valid credentials exist in `.env`
- **THEN** the system SHALL authenticate using client credentials
- **AND** fetch all rides from the Hammerhead API
- **AND** display each ride's unique ID and name

#### Scenario: Authentication failure
- **WHEN** the user runs the CLI with `--all` flag
- **AND** credentials are invalid or missing
- **THEN** the system SHALL display an appropriate error message

#### Scenario: API request failure
- **WHEN** the user runs the CLI with `--all` flag
- **AND** the API request fails due to network issues
- **THEN** the system SHALL display an error message explaining the failure

### Requirement: Environment Variable Loading
The system SHALL load credentials from environment variables defined in a `.env` file.

#### Scenario: Load credentials from .env
- **WHEN** the CLI starts
- **THEN** the system SHALL load `HAMMERHEAD_CLIENT_ID` and `HAMMERHEAD_CLIENT_SECRET` from `.env`
- **AND** use these values for API authentication

### Requirement: OAuth2 Client Credentials Authentication
The system SHALL authenticate with the Hammerhead API using OAuth2 client credentials flow.

#### Scenario: Obtain access token
- **WHEN** a new API request is made
- **AND** no valid token exists
- **THEN** the system SHALL request an access token using client credentials
- **AND** cache the token for subsequent requests
