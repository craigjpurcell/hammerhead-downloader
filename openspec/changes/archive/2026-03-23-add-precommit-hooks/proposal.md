# Proposal: add-precommit-hooks

## Summary
Add pre-commit hooks to prevent accidentally committing sensitive files like `.env`, credentials, and other secrets to the repository.

## Why
Security assessment found risk of accidentally committing `.env` files containing OAuth credentials. Pre-commit hooks provide a safety net to catch these mistakes before they reach the repository.

## What Changes
- Add `.pre-commit-config.yaml` configuration
- Include hooks for:
  - Detecting `.env` files
  - Detecting common secret patterns
  - Blocking commits with staged `.env` files

## Scope
- Pre-commit configuration file
- Documentation in README

## Out of Scope
- CI-based secret scanning (GitHub Advanced Security)
- GitHub Actions secret detection
