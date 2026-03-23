# Proposal: add-repo-protection

## Summary
Add GitHub protection configuration to ensure only the owner can merge changes to the main branch, and add CI workflow to validate changes on pull requests.

## Why
Making the repository public requires protection to:
- Prevent unauthorized changes from being merged
- Ensure all changes pass tests before merging
- Maintain code quality standards when the owner isn't actively reviewing

## What Changes
- Create `.github/CODEOWNERS` file requiring review from owner
- Create `.github/workflows/ci.yml` to run tests on PRs
- Document branch protection settings for GitHub UI configuration

## Scope
- Code owners configuration file
- GitHub Actions CI workflow
- Documentation of required GitHub UI settings

## Out of Scope
- Other branch workflows (develop, feature branches)
- Security vulnerability scanning
- Release automation

## User Experience
### For contributors (future):
```bash
# Create PR
git checkout -b fix/bug
# ... make changes ...
git push -u origin fix/bug
# PR will run CI tests automatically
# Must get approval from @craigjpurcell to merge
```

### For owner:
- All PRs require your approval
- CI must pass before merge is allowed
- You can bypass protection rules
