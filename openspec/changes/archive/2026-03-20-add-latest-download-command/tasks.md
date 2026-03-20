# Tasks: add-latest-download-command

## Implementation Order

### Phase 1: Core Logic
1. [x] **Add `get_downloads_dir()` helper** in `cli.py`
   - Read `HAMMERHEAD_DOWNLOADS` from environment
   - Raise `ClickException` with clear message if not set
   - Return `Path` object

2. [x] **Add `get_downloaded_ids()` helper** in `cli.py`
   - Scan `HAMMERHEAD_DOWNLOADS` for `*.fit` files
   - Extract activity IDs from filenames
   - Return set of IDs

3. [x] **Add `get_all_activities()` method** to `HammerheadClient`
   - Fetch all activities across all pages
   - Return list of `Activity` objects

4. [x] **Add `--latest` flag to `download_activity` command**
   - Add `@click.option("--latest", is_flag=True)`
   - Validate `HAMMERHEAD_DOWNLOADS` is set
   - Fetch all activities
   - Filter out already-downloaded IDs
   - Filter out activities < 5 minutes (300,000 ms)
   - Download each new FIT file
   - Report progress and summary

### Phase 2: Output Formatting
5. [x] **Add clear reporting to `--latest`**
   - Show "Downloading N new activities..." header
   - Show [+] for each downloaded file with name/size/duration
   - Show [-] for skipped short activities
   - Show final summary count

### Phase 3: Validation
6. [x] **Add unit tests for `get_downloaded_ids()`**
   - Mock filesystem with sample `.fit` files

7. [x] **Add unit tests for duration filtering**
   - Test activity > 5 min is downloaded
   - Test activity < 5 min is skipped

8. [x] **Add integration test for `--latest`**
   - Mock API responses
   - Verify correct files downloaded

### Phase 4: Documentation
9. [x] **Update README.md**
   - Document `--latest` flag
   - Document `HAMMERHEAD_DOWNLOADS` env var
   - Add example output
