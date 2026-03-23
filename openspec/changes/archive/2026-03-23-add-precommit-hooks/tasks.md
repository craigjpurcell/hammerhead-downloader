# Tasks: add-precommit-hooks

## Implementation Order

### Phase 1: Configuration
1. [ ] **Create `.pre-commit-config.yaml`**
   - Add pre-commit-hooks framework
   - Add detect-env hook to flag .env files
   - Add detect-secrets hook for common patterns
   - Add check-added-files hook for .env

### Phase 2: Documentation
2. [ ] **Update README.md**
   - Document pre-commit hooks setup
   - Explain how to install and use

### Phase 3: Validation
3. [ ] **Test hooks locally**
   - Verify .env is blocked on commit attempt
