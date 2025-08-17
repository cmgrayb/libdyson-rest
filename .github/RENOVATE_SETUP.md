# Renovate Bot Self-hosted Setup Guide

This guide explains how to set up and configure Renovate Bot for self-hosted dependency management without external services.

## Overview

The libdyson-rest project uses Renovate Bot to automatically:
- Monitor dependency updates across Python packages, GitHub Actions, and pre-commit hooks
- Create pull requests with dependency updates
- Group related updates logically
- Provide security vulnerability alerts
- Maintain version synchronization with your `sync_versions.py` script

## Self-hosted Configuration

### Key Features
- ✅ **No external reporting**: All data stays within your GitHub repository
- ✅ **Standard GitHub token**: Uses built-in `GITHUB_TOKEN` (no separate Renovate token needed)
- ✅ **Local security scanning**: No external vulnerability databases
- ✅ **Repository-contained config**: All settings in `renovate.json`

### Files Involved
- `renovate.json` - Main Renovate configuration
- `.github/workflows/renovate.yml` - GitHub Actions workflow to run Renovate
- `scripts/sync_versions.py` - Version synchronization (called after quality tool updates)

## Renovate Schedule & Behavior

### Automatic Schedule
- **Runs**: Every Monday at 6 AM UTC
- **PR Limits**: Max 3 concurrent, 2 per hour
- **Grouping**: Related dependencies grouped into single PRs

### Manual Execution
Trigger manually via GitHub Actions:
1. Go to repository → Actions → "Renovate Bot (Self-hosted)"
2. Click "Run workflow"
3. Choose options:
   - **Dry run**: Preview what would be updated without creating PRs
   - **Log level**: debug/info/warn/error for troubleshooting

## Dependency Grouping Strategy

### 1. Development Dependencies (`requirements-dev.txt`)
- **Group**: "development dependencies"
- **Schedule**: Monday mornings
- **Min age**: 3 days
- **Auto-merge**: Disabled (manual review required)
- **Post-merge action**: ⚠️ Run `python scripts/sync_versions.py`

### 2. Production Dependencies (`requirements.txt`)
- **Group**: "production dependencies"
- **Schedule**: Monday mornings
- **Min age**: 7 days (more conservative)
- **Auto-merge**: Disabled

### 3. Code Quality Tools (Black, Flake8, isort, mypy, pytest)
- **Group**: "code quality tools"
- **Labels**: `quality-tools`
- **Critical**: ⚠️ **Must** run `python scripts/sync_versions.py` after merge
- **Post-merge checklist**: Provided in PR description

### 4. Pre-commit Hooks (`.pre-commit-config.yaml`)
- **Group**: "pre-commit hooks"
- **Min age**: 3 days
- **Post-merge action**: Run `python scripts/sync_versions.py`

### 5. GitHub Actions
- **Group**: "GitHub Actions"
- **Min age**: 3 days
- **Covers**: All `uses:` statements in workflow files

### 6. Security Tools (Safety, Bandit)
- **Group**: "security tools"
- **Min age**: 1 day (faster security updates)

## Update Priority & Handling

### Security Vulnerabilities
- **Priority**: Immediate (highest)
- **Labels**: `security`, `vulnerability`, `high-priority`
- **Min age**: None (created immediately)
- **Review**: Auto-assigned to repository owner

### Major Version Updates
- **Min age**: 14 days (conservative approach)
- **Labels**: `major-update`
- **Review**: Required with breaking change checklist
- **Auto-merge**: Always disabled

### Minor/Patch Updates
- **Min age**: 3 days
- **Labels**: `minor-patch-update`
- **Review**: Optional for well-tested packages

## Dependency Dashboard

Renovate creates a "Dependency Dashboard" issue that provides:
- Overview of all managed dependencies
- Status of pending updates
- Failed update attempts
- Manual approval workflows (if needed)

The dashboard is updated automatically and serves as a central management interface.

## Integration with Version Synchronization

### Critical Integration Points

1. **Quality Tool Updates**: When Renovate updates `black`, `flake8`, `isort`, `mypy`, `pytest`, or `pre-commit`, it automatically adds instructions to run version synchronization.

2. **Post-merge Workflow**:
   ```bash
   # After merging Renovate PRs for quality tools:
   python scripts/sync_versions.py --verbose
   git add requirements-dev.txt pyproject.toml .pre-commit-config.yaml
   git commit -m "🔧 Sync tool versions after dependency update"
   ```

3. **Automated Reminders**: The workflow automatically comments on quality tool PRs with specific post-merge instructions.

## Self-hosted Security

### What Data Stays Local
- ✅ Dependency analysis
- ✅ Vulnerability scanning (using local databases)
- ✅ PR creation and management
- ✅ Configuration and logs

### External Services Disabled
- ❌ OSV vulnerability database queries
- ❌ External analytics or reporting
- ❌ Third-party integrations
- ❌ Dependency dashboard approval workflows

## Troubleshooting

### Common Issues

#### Renovate Not Running
1. Check GitHub Actions permissions in repository settings
2. Verify `renovate.json` syntax with schema validation
3. Check workflow logs in Actions tab

#### No PRs Created
1. Run with `dry_run: true` to see what would be updated
2. Check minimum release age settings
3. Verify file patterns match your repository structure

#### Version Sync Issues After Merge
1. Manually run: `python scripts/sync_versions.py --dry-run --verbose`
2. Check for differences between config files
3. Re-run without `--dry-run` to fix synchronization

#### Quality Tools PR Missing Instructions
1. Check PR labels include `quality-tools`
2. Verify package names in Renovate config match actual packages
3. Look for automated comments from the workflow

### Manual Override

#### Skip Renovate for Specific Update
Add to `renovate.json`:
```json
{
  "packageRules": [
    {
      "matchPackageNames": ["package-name"],
      "enabled": false
    }
  ]
}
```

#### Emergency Security Update
Renovate creates security PRs immediately (no minimum age), but you can also:
1. Update manually
2. Run `python scripts/sync_versions.py` if needed
3. Push fix directly to main branch

## Monitoring & Metrics

### What to Monitor
- Weekly dependency dashboard updates
- Security vulnerability PRs (high priority)
- Failed update attempts in workflow logs
- Version synchronization after quality tool merges

### Success Indicators
- Regular weekly PRs created
- No version mismatches between config files
- Security updates applied promptly
- Quality tools stay current

## Configuration Customization

### Adjust Update Frequency
Edit `schedule` in `renovate.json`:
```json
"schedule": ["before 6am on tuesday"]  // Change day
"schedule": ["every 2 weeks"]          // Change frequency
```

### Modify Grouping
Add new package rules:
```json
{
  "matchPackageNames": ["requests", "cryptography"],
  "groupName": "core dependencies",
  "minimumReleaseAge": "5 days"
}
```

### Change Review Requirements
```json
{
  "reviewers": ["username1", "username2"],
  "assignees": ["username1"]
}
```

This self-hosted setup provides automated dependency management while keeping all data and processing within your GitHub repository, perfectly suited for paranoid developers who want control over their dependency management pipeline! 🛡️
