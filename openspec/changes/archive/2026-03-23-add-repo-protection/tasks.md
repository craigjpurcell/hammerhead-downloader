# Tasks: add-repo-protection

## Implementation Order

### Phase 1: Configuration Files
1. [x] **Create `.github/CODEOWNERS`**
   - Add single line: `* @craigjpurcell`
   - Create `.github/` directory if not exists

2. [x] **Create CI workflow `.github/workflows/ci.yml`**
   - Trigger on pull_request and push
   - Use uv for Python environment
   - Install with dev dependencies
   - Run pytest
   - Run ruff check and format

### Phase 2: Documentation
3. [x] **Document branch protection settings in README**
   - Explain required GitHub UI configuration
   - List recommended settings table
   - Document required status checks

### Phase 3: Validation
4. [x] **Verify workflow syntax**
   - YAML syntax validated
