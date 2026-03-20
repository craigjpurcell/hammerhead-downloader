# Project Context

## Purpose
CLI tool that downloads ride data from the Hammerhead API, maintains a local directory of FIT files, and avoids duplicating already-downloaded data.

## Tech Stack
- Python 3.11+
- Click (CLI framework)
- Requests (HTTP client)
- python-dotenv (environment configuration)
- pytest (testing)

## Project Conventions

### Code Style
- Format with `ruff format`
- Lint with `ruff check --fix`
- Type hints required for all function signatures
- Docstrings for public modules and classes (Google style)

### Architecture Patterns
- Single-command CLI with subcommands via Click
- Configuration via environment variables (`.env` file)
- Downloaded files stored in a configurable output directory
- State tracking via a local SQLite database or JSON manifest

### Testing Strategy
- Unit tests in `tests/` directory
- Use pytest fixtures for API mocking
- Integration tests for end-to-end download scenarios

### Git Workflow
- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
- Feature branches: `feat/<description>`
- PRs required for main branch

## Domain Context
- **FIT files**: Binary fitness data format from cycling computers
- **Hammerhead API**: REST API requiring OAuth2 client credentials
- **Ride data**: Includes GPS coordinates, speed, heart rate, power, cadence

## Important Constraints
- Must not re-download already-acquired FIT files
- API rate limits must be respected
- FIT files must be preserved exactly (binary integrity)

## External Dependencies
- Hammerhead API (`HAMERHEAD_CLIENT_ID`, `HAMERHEAD_CLIENT_SECRET`)
- Local file system for FIT file storage
- API specification https://api.hammerhead.io/v1/docs

