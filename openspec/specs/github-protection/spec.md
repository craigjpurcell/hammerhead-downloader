# github-protection Specification

## Purpose
TBD - created by archiving change add-repo-protection. Update Purpose after archive.
## Requirements
### Requirement: CODEOWNERS File
The repository SHALL have a `.github/CODEOWNERS` file that assigns ownership to the repository owner.

#### Scenario: CODEOWNERS file exists
- **WHEN** the repository is cloned or viewed on GitHub
- **THEN** a `.github/CODEOWNERS` file SHALL exist
- **AND** contain `@craigjpurcell` as the default owner

### Requirement: CI Workflow
The repository SHALL have a GitHub Actions workflow that runs tests on pull requests.

#### Scenario: CI workflow runs on pull request
- **WHEN** a pull request is opened or updated
- **AND** commits are pushed to the branch
- **THEN** the CI workflow SHALL run `pytest`
- **AND** report success or failure

#### Scenario: CI workflow runs on push
- **WHEN** code is pushed directly to a branch
- **THEN** the CI workflow SHALL run `pytest`
- **AND** report success or failure

### Requirement: Branch Protection
The main branch SHALL be protected via GitHub UI settings.

#### Scenario: Configure main branch protection
- **WHEN** the owner configures branch protection in GitHub settings
- **THEN** the following settings SHALL be applied:
  - Require pull request reviews before merging
  - Require review from code owner
  - Require status checks to pass
  - Include administrators: No (owner bypasses)
  - Allow force pushes: No
  - Allow deletions: No

### Requirement: CI Workflow Uses UV
The CI workflow SHALL use `uv` for Python package management.

#### Scenario: CI installs dependencies with uv
- **WHEN** the CI workflow runs
- **THEN** it SHALL use `uv pip install` to install dependencies
- **AND** install with `[dev]` extras for testing

