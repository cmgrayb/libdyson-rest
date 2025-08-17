# Branch Protection Settings Documentation
#
# This file documents the recommended branch protection settings for the repository.
# These should be configured in GitHub repository settings > Branches.

## Main Branch Protection Rules

### Required Status Checks
The following status checks must pass before merging:

#### Always Required:
- `quality-checks / Quality Checks (3.11)` - Primary quality check with Python 3.11
- `pre-commit / Pre-commit Hooks` - Pre-commit hook validation
- `build-test / Build Test (ubuntu-latest, 3.11)` - Build verification on Linux with Python 3.11

#### Conditionally Required:
- `version-sync-check / Version Synchronization Check` - Only when configuration files change
- `security-scan / Security Scan` - Security vulnerability scanning (warning only)

### Additional Protection Settings:
- ✅ Require branches to be up to date before merging
- ✅ Require pull request reviews before merging (minimum 1 reviewer)
- ✅ Dismiss stale reviews when new commits are pushed
- ✅ Require review from code owners (if CODEOWNERS file exists)
- ✅ Include administrators in restrictions
- ✅ Allow force pushes: disabled
- ✅ Allow deletions: disabled

### Auto-merge Settings:
- ✅ Allow auto-merge
- ✅ Automatically delete head branches after merge

## GitHub Repository Settings

### General Settings:
```yaml
# In repository settings > General
merge_commit_title: "PR_TITLE"
merge_commit_message: "PR_BODY"
squash_merge_commit_title: "PR_TITLE"
squash_merge_commit_message: "PR_BODY"
delete_branch_on_merge: true
```

### Security Settings:
```yaml
# In repository settings > Security
vulnerability_alerts: true
security_updates: true
secret_scanning: true
push_protection: true
```

### Webhook Events (for advanced integrations):
- Pull requests
- Push
- Status
- Check runs
- Check suites

## Quality Gate Matrix

| Check Type | Python Versions | OS Support | Failure Impact |
|------------|----------------|------------|----------------|
| Code Quality | 3.9-3.13 | Linux primary | Blocks merge |
| Pre-commit | 3.11 | Linux | Blocks merge |
| Build Test | 3.9-3.13 | Linux/Windows/macOS | Blocks merge |
| Security Scan | 3.11 | Linux | Warning only |
| Version Sync | 3.11 | Linux | Blocks merge (when applicable) |

## Manual Override Process

### Emergency Bypass:
1. Add `ci-force` label to PR to force CI on draft PRs
2. Admin can override branch protection for hotfixes
3. Document reason in PR description

### Skip CI:
- Draft PRs automatically skip CI (unless `ci-force` label present)
- Use `[skip ci]` in commit message for documentation-only changes

## Monitoring and Alerts

### Workflow Failure Notifications:
- Failed workflows create PR comments with actionable guidance
- Weekly dependency update checks create issues when updates available
- Security scans upload reports as artifacts

### Metrics to Track:
- CI success rate per branch
- Average PR review time
- Test coverage trends
- Security vulnerability trends
- Dependency freshness
