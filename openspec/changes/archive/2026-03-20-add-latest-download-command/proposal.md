# Proposal: add-latest-download-command

## Summary
Add a `--latest` flag to `hammerhead activities download` that syncs all undownloaded activities from the API into the `HAMMERHEAD_DOWNLOADS` directory, skipping duplicates and short activities (<5 minutes).

## Motivation
Users want a one-command way to sync all their new ride data from Hammerhead without manually identifying which activities have already been downloaded. The CLI already supports downloading individual FIT files, but this requires knowing which activities exist and which have already been downloaded.

## Scope
- Add `--latest` flag to the `download` subcommand
- Read `HAMMERHEAD_DOWNLOADS` env var to find existing FIT files
- Fetch all activities from the API (handling pagination)
- Compare API activity IDs against downloaded file names
- Skip activities shorter than 5 minutes (300,000 ms)
- Download new FIT files to `HAMMERHEAD_DOWNLOADS`
- Report clearly which files were downloaded

## Out of Scope
- Modifying the existing single-activity download behavior
- FIT file parsing or analysis
- Background sync / watch mode
- Configuring minimum duration threshold

## User Experience
```bash
# Configure downloads directory
export HAMMERHEAD_DOWNLOADS=~/hammerhead-rides

# Sync all new rides
hammerhead activities download --latest
```

Expected output:
```
Downloading 3 new activities...
✓ Morning Ride (167249.activity.abc123.fit) - 45.2km, 120.5m
✓ Evening Ride (167249.activity.def456.fit) - 32.1km, 95.0m
✗ Skipped: Short Spin (duration: 4.2m < 5m minimum)
Downloaded 2 FIT files to ~/hammerhead-rides
```
