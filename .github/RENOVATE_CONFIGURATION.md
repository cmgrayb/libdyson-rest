# Renovate Configuration Documentation

This document explains the automated dependency management configuration in `renovate.json` for the libdyson-rest project.

## Overview

Renovate Bot is configured as a self-hosted solution that automatically monitors dependencies and creates pull requests for updates. The configuration balances automation with safety, ensuring timely updates while maintaining control over the dependency management process.

## Configuration Structure

### Base Configuration

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "group:monorepos",
    "group:recommended", 
    "replacements:all",
    "workarounds:all"
  ]
}
```

**Purpose**: Inherits Renovate's recommended settings and applies common groupings and workarounds.

**Presets Explained**:
- `config:recommended` - Renovate's battle-tested base configuration
- `group:monorepos` - Groups monorepo dependencies together
- `group:recommended` - Groups related dependencies (e.g., ESLint plugins)
- `replacements:all` - Handles package renames and replacements automatically
- `workarounds:all` - Applies known workarounds for common dependency issues

### Scheduling and Rate Limiting

```json
{
  "timezone": "UTC",
  "prHourlyLimit": 0,
  "prConcurrentLimit": 0
}
```

**Purpose**: Controls when and how frequently Renovate creates pull requests.

**Settings Explained**:
- `timezone: "UTC"` - All scheduling uses UTC timezone
- `prHourlyLimit: 0` - No limit on PRs per hour (unlimited)
- `prConcurrentLimit: 0` - No limit on concurrent PRs (unlimited)

### Commit and PR Formatting

```json
{
  "commitMessagePrefix": "⬆️",
  "commitMessageTopic": "{{depName}}",
  "commitMessageExtra": "to v{{newVersion}}",
  "labels": ["dependencies", "renovate"],
  "reviewers": ["cmgrayb"],
  "assignees": ["cmgrayb"]
}
```

**Purpose**: Standardizes commit messages and PR metadata.

**Result**: Creates commit messages like `⬆️ black to v25.1.0` and ensures consistent labeling and assignment.

### Merge Control

```json
{
  "platformAutomerge": false,
  "automerge": false,
  "dependencyDashboard": false
}
```

**Purpose**: Maintains manual control over all dependency updates.

**Settings Explained**:
- `platformAutomerge: false` - Disables GitHub's auto-merge feature
- `automerge: false` - Requires manual review and approval for all PRs
- `dependencyDashboard: false` - Uses individual PRs instead of a dashboard issue

### Git Author Protection

```json
{
  "gitIgnoredAuthors": [
    "Renovate Bot <bot@renovateapp.com>",
    "renovate[bot] <29139614+renovate[bot]@users.noreply.github.com>",
    "41898282+github-actions[bot]@users.noreply.github.com",
    "renovate@libdyson-rest.local",
    "cmgrayb@outlook.com",
    "79777799+cmgrayb@users.noreply.github.com",
    "Christopher Gray <79777799+cmgrayb@users.noreply.github.com>"
  ]
}
```

**Purpose**: Prevents infinite loops by ignoring commits from automated systems and the repository owner.

## Package Rules (Dependency Management Strategy)

### 1. GitHub Runner Versions (Disabled)

```json
{
  "matchDatasources": ["github-runners"],
  "enabled": false,
  "description": "Ignore GitHub runner version updates (ubuntu-latest, etc.)"
}
```

**Purpose**: Keeps GitHub Actions using `ubuntu-latest`, `windows-latest` etc. without updates to specific versions.

### 2. GitHub Actions Matrix Variables (Disabled)

```json
{
  "matchDatasources": ["github-releases"],
  "matchDepTypes": ["uses-with"],
  "matchCurrentValue": "/^\\$\\{\\{.*\\}\\}$/",
  "enabled": false,
  "description": "Ignore GitHub Actions matrix variables"
}
```

**Purpose**: Prevents updates to GitHub Actions that use matrix variables like `${{ matrix.python-version }}`.

### 3. Development Dependencies

```json
{
  "matchManagers": ["pip_requirements", "pep621"],
  "matchFileNames": ["requirements-dev.txt", "pyproject.toml"],
  "groupName": "development dependencies",
  "labels": ["dependencies", "dev-dependencies"],
  "minimumReleaseAge": "3 days"
}
```

**Purpose**: Groups development dependencies from both files into single PRs.

**Features**:
- 3-day stability wait after package release
- Groups updates from `requirements-dev.txt` and `pyproject.toml`
- Custom PR template with post-merge checklist

### 4. Production Dependencies

```json
{
  "matchManagers": ["pip_requirements"],
  "matchFileNames": ["requirements.txt"],
  "groupName": "production dependencies",
  "minimumReleaseAge": "7 days"
}
```

**Purpose**: Conservative handling of production dependencies.

**Features**:
- 7-day stability wait (more conservative than dev dependencies)
- Separate grouping from development dependencies

### 5. GitHub Actions

```json
{
  "matchManagers": ["github-actions"],
  "groupName": "GitHub Actions",
  "minimumReleaseAge": "3 days"
}
```

**Purpose**: Groups all GitHub Actions updates together with moderate stability wait.

### 6. Major Version Updates

```json
{
  "matchUpdateTypes": ["major"],
  "labels": ["dependencies", "major-update"],
  "automerge": false,
  "minimumReleaseAge": "14 days"
}
```

**Purpose**: Extremely conservative handling of major version updates.

**Features**:
- 14-day stability wait
- Explicit automerge disable
- Special warning labels
- Custom PR template warning about breaking changes

### 7. Minor and Patch Updates

```json
{
  "matchUpdateTypes": ["minor", "patch"],
  "labels": ["dependencies", "minor-patch-update"],
  "minimumReleaseAge": "3 days"
}
```

**Purpose**: Standard handling for smaller, less risky updates.

### 8. Code Quality Tools (Special Handling)

```json
{
  "matchPackageNames": [
    "black",
    "flake8", 
    "isort",
    "mypy",
    "pytest",
    "bandit"
  ],
  "groupName": "code quality tools",
  "labels": ["dependencies", "quality-tools"]
}
```

**Purpose**: Special handling for tools that require version synchronization.

**Features**:
- Groups all code quality tools together
- Special `quality-tools` label for identification
- Custom PR template mentioning version synchronization requirements
- These PRs require running `python scripts/sync_versions.py` after merge

### 9. Security Tools

```json
{
  "matchPackageNames": ["safety", "bandit"],
  "groupName": "security tools",
  "minimumReleaseAge": "1 day"
}
```

**Purpose**: Faster updates for security-related tools.

**Features**:
- Only 1-day stability wait (faster than other tools)
- Separate grouping for security tools

## Vulnerability Management

```json
{
  "vulnerabilityAlerts": {
    "labels": ["security", "vulnerability", "high-priority"],
    "reviewers": ["cmgrayb"],
    "assignees": ["cmgrayb"],
    "prCreation": "immediate",
    "minimumReleaseAge": null
  }
}
```

**Purpose**: Immediate response to security vulnerabilities.

**Features**:
- Creates PRs immediately when vulnerabilities are detected
- No stability wait period for security fixes
- High-priority labels for urgent attention
- Automatic assignment for immediate review

## Lock File Maintenance

```json
{
  "lockFileMaintenance": {
    "enabled": false
  }
}
```

**Purpose**: Disabled since the project uses `requirements.txt` files instead of lock files like `package-lock.json`.

## Workflow Integration

### Post-Merge Actions

Different types of dependency updates require different post-merge actions:

#### Code Quality Tools (`quality-tools` label)
1. Merge the Renovate PR
2. Run `python scripts/sync_versions.py --verbose`
3. Verify all quality checks pass
4. Update Copilot instructions if version numbers changed significantly

#### Development Dependencies
1. Merge the Renovate PR
2. Run full test suite locally to verify compatibility
3. Check for any new deprecation warnings

#### Major Version Updates
1. **Review breaking changes carefully before merging**
2. Run full test suite locally
3. Check changelog for breaking changes
4. Update documentation if needed
5. Verify all GitHub Actions still pass

#### Security Updates
1. Merge immediately after review
2. Run security scans to verify fix
3. Update security documentation if needed

### GitHub Actions Integration

The Renovate configuration works with the project's GitHub Actions workflows:

- **Quality Checks**: All Renovate PRs trigger the full CI pipeline
- **Version Sync Validation**: PRs that modify quality tools trigger version sync checks
- **Security Scanning**: Security-related updates trigger additional security scans

## Troubleshooting

### Common Issues

#### Renovate PRs Not Created
1. Check the Renovate workflow in `.github/workflows/renovate.yml`
2. Verify the workflow has proper permissions
3. Check for errors in the workflow run logs

#### Version Sync Failures
1. Quality tool updates require manual version synchronization
2. Run `python scripts/sync_versions.py --dry-run --verbose` to preview changes
3. Run `python scripts/sync_versions.py --verbose` to apply changes

#### Conflicting PRs
1. Renovate groups related dependencies to minimize conflicts
2. If conflicts occur, close older PRs and let Renovate recreate them
3. Check for manual changes that might conflict with automated updates

### Manual Renovate Triggers

You can manually trigger Renovate checks:

1. Go to Actions tab in GitHub
2. Select "Renovate" workflow  
3. Click "Run workflow"
4. This forces an immediate dependency scan

## Best Practices

### Reviewing Renovate PRs

1. **Check CI Status**: Ensure all quality checks pass
2. **Review Changelog**: Look for breaking changes in major updates
3. **Test Locally**: For significant updates, test locally before merging
4. **Version Sync**: Remember to run sync script for quality tools
5. **Security Priority**: Merge security updates quickly after review

### Maintenance

1. **Regular Reviews**: Review Renovate configuration quarterly
2. **Version Updates**: Keep Renovate itself updated in the workflow
3. **Rule Adjustments**: Adjust `minimumReleaseAge` based on project needs
4. **Label Management**: Keep labels consistent with project standards

## Configuration Files

The Renovate configuration interacts with several project files:

- `renovate.json` - Main configuration file
- `.github/workflows/renovate.yml` - GitHub Actions workflow
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies  
- `pyproject.toml` - Project metadata and tool configuration
- `scripts/sync_versions.py` - Version synchronization script

## Security Considerations

- All dependency updates go through PR review process
- Vulnerability alerts are prioritized with immediate PR creation
- Security tools get faster update cycles (1-day minimum vs 3-7 days)
- No automatic merging prevents unauthorized changes
- Git author filtering prevents infinite update loops

This configuration ensures reliable, secure, and maintainable dependency management while minimizing manual overhead and maximizing automation benefits.