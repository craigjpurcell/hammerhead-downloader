# Change: Add `--all` flag to list all rides with IDs

## Why
Users need a way to quickly view all their rides, the data and timestamp of the ride, and their unique identifiers from the Hammerhead API without downloading any files.

## What Changes
- Add `--all` flag to the CLI command
- Implement `list_rides` function to fetch all rides from Hammerhead API
- Authenticate using `HAMMERHEAD_CLIENT_ID` and `HAMMERHEAD_CLIENT_SECRET` from `.env`
- Display ride IDs and names in a user-friendly format

## Impact
- Affected specs: This is a new capability (rides-list)
- Affected code: New CLI command, new API client module
