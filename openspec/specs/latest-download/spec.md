# latest-download Specification

## Purpose
TBD - created by archiving change add-latest-download-command. Update Purpose after archive.
## Requirements
### Requirement: Downloads Directory Configuration
The system SHALL require the `HAMMERHEAD_DOWNLOADS` environment variable to specify where FIT files are stored.

#### Scenario: Missing downloads directory
- **WHEN** the user runs `hammerhead activities download --latest`
- **AND** `HAMMERHEAD_DOWNLOADS` is not set
- **THEN** the system SHALL display an error: "HAMMERHEAD_DOWNLOADS environment variable is not set. Please set it to your downloads directory."
- **AND** exit with a non-zero status code

### Requirement: Detect Already-Downloaded Activities
The system SHALL detect which activities have already been downloaded by scanning the `HAMMERHEAD_DOWNLOADS` directory for existing `.fit` files.

#### Scenario: Identify downloaded files by filename
- **WHEN** the user runs `hammerhead activities download --latest`
- **THEN** the system SHALL scan `HAMMERHEAD_DOWNLOADS` for all files matching `*.fit`
- **AND** extract activity IDs from filenames (e.g., `167249.activity.abc.fit` → `167249.activity.abc`)

#### Scenario: Skip already-downloaded activities
- **WHEN** the user runs `hammerhead activities download --latest`
- **AND** an activity ID matches an existing `.fit` filename
- **THEN** the system SHALL skip downloading that activity
- **AND** not report it as a duplicate

### Requirement: Minimum Activity Duration Filter
The system SHALL skip activities with a duration less than 5 minutes (300,000 milliseconds).

#### Scenario: Skip short activities
- **WHEN** the user runs `hammerhead activities download --latest`
- **AND** an activity has `duration < 300000`
- **THEN** the system SHALL skip downloading that activity
- **AND** report it as "Skipped: [name] (duration: Xm < 5m minimum)"

### Requirement: Download Latest Activities Command
The system SHALL provide a `--latest` flag on `hammerhead activities download` that downloads all undownloaded activities.

#### Scenario: Download new activities successfully
- **WHEN** the user runs `hammerhead activities download --latest`
- **AND** `HAMMERHEAD_DOWNLOADS` is set to a valid directory
- **AND** there are activities not yet downloaded
- **AND** activities have duration >= 5 minutes
- **THEN** the system SHALL download each FIT file to `HAMMERHEAD_DOWNLOADS`
- **AND** name the file `<activity-id>.fit`
- **AND** report "✓ [activity-name] ([filename].fit) - [distance]km, [duration]m" for each

#### Scenario: No new activities to download
- **WHEN** the user runs `hammerhead activities download --latest`
- **AND** `HAMMERHEAD_DOWNLOADS` is set to a valid directory
- **AND** all activities are already downloaded or too short
- **THEN** the system SHALL display "No new activities to download."
- **AND** exit with status code 0

#### Scenario: Downloads across multiple pages
- **WHEN** the user runs `hammerhead activities download --latest`
- **AND** the user has more activities than fit on one page
- **THEN** the system SHALL fetch all pages from the API
- **AND** process all activities for download eligibility

### Requirement: Clear Download Reporting
The system SHALL clearly report which files were downloaded and which were skipped.

#### Scenario: Report download progress
- **WHEN** the user runs `hammerhead activities download --latest`
- **AND** N activities are eligible for download
- **THEN** the system SHALL display "Downloading N new activities..." before starting
- **AND** display each successful download with checkmark (✓)
- **AND** display each skip (short duration) with X mark (✗)
- **AND** display final summary: "Downloaded M FIT files to [directory]"

#### Scenario: Report skipped duplicates
- **WHEN** the user runs `hammerhead activities download --latest`
- **AND** some activities are already downloaded
- **THEN** the system SHALL silently skip duplicates (no output required)

