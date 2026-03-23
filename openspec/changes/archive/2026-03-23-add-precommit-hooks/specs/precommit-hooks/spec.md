# precommit-hooks Specification

## ADDED Requirements

### Requirement: Pre-commit Configuration File
The repository SHALL have a `.pre-commit-config.yaml` file that prevents committing sensitive files.

#### Scenario: Pre-commit config exists
- **WHEN** the repository root is examined
- **THEN** a `.pre-commit-config.yaml` file SHALL exist
- **AND** contain configuration for blocking `.env` files

### Requirement: Prevent .env Commit
The pre-commit hooks SHALL prevent commits that include `.env` files.

#### Scenario: Attempt to commit .env file
- **WHEN** a user runs `git commit` with `.env` staged
- **THEN** the commit SHALL be rejected
- **AND** display an error message explaining why

### Requirement: Detect Common Secrets
The pre-commit hooks SHALL detect common secret patterns in staged files.

#### Scenario: Stage file with API key pattern
- **WHEN** a user stages a file containing patterns like `api_key=`, `password=`, `secret=`
- **THEN** the commit SHALL be rejected
- **AND** display a warning about potential secrets

### Requirement: Pre-commit Installation
The pre-commit hooks SHALL be installable via `pre-commit install`.

#### Scenario: Install pre-commit hooks
- **WHEN** a user runs `pre-commit install`
- **THEN** the hooks SHALL be activated
- **AND** run automatically on each commit
