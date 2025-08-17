# 🚀 Automated Release Pipeline Setup

This document explains how to set up and use the automated release pipeline system for libdyson-rest.

## 📋 Overview

The automated release pipeline provides branch-based release management with automatic versioning, testing, and publishing:

- **`release/alpha`** → Auto-increment alpha versions → TestPyPI
- **`release/beta`** → Auto-increment beta versions → PyPI  
- **`release/rc`** → Auto-increment RC versions → PyPI
- **`main`** → Stable releases → PyPI (manual trigger or version change detection)

## 🔧 Initial Setup

### 1. Branch Protection Setup

Create and protect the release branches in your GitHub repository:

```bash
# Create release branches
git checkout -b release/alpha
git push -u origin release/alpha

git checkout main
git checkout -b release/beta  
git push -u origin release/beta

git checkout main
git checkout -b release/rc
git push -u origin release/rc

git checkout main
```

### 2. GitHub Repository Settings

Navigate to **Settings** → **Branches** and create protection rules:

#### For `main` branch:
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Required status checks: `Quality checks (Python 3.11)`, `Build test (ubuntu-latest, Python 3.11)`

#### For `release/*` branches:
- ✅ Restrict pushes to administrators only
- ✅ Allow force pushes (for automated commits)
- ✅ Allow deletions (for reset/cleanup operations)

### 3. Trusted Publisher Configuration

#### TestPyPI (for alpha builds):
1. Go to https://test.pypi.org/manage/account/publishing/
2. Add trusted publisher:
   - **Owner**: `cmgrayb`
   - **Repository**: `libdyson-rest`
   - **Workflow**: `auto-release-alpha.yml`
   - **Environment**: `testpypi`

#### PyPI (for beta/rc/stable builds):
1. Go to https://pypi.org/manage/account/publishing/
2. Add trusted publisher:
   - **Owner**: `cmgrayb`
   - **Repository**: `libdyson-rest`
   - **Workflow**: `auto-release-beta.yml`
   - **Environment**: `pypi`
3. Add another trusted publisher:
   - **Owner**: `cmgrayb`
   - **Repository**: `libdyson-rest`
   - **Workflow**: `auto-release-rc.yml`
   - **Environment**: `pypi`
4. Add another trusted publisher:
   - **Owner**: `cmgrayb`
   - **Repository**: `libdyson-rest`
   - **Workflow**: `auto-release-stable.yml`
   - **Environment**: `pypi`

### 4. GitHub Environments

Create environments in **Settings** → **Environments**:

#### `testpypi` environment:
- **Protection rules**: None (allow automatic deployment)
- **Environment secrets**: None needed (uses trusted publishing)

#### `pypi` environment:
- **Protection rules**: 
  - ✅ Required reviewers: Add yourself as reviewer
  - ⏰ Wait timer: 0 minutes (optional: add 5-10 minutes for final review)
- **Environment secrets**: None needed (uses trusted publishing)

## 🎯 Usage Workflows

### 🧪 Alpha Release (Development Testing)

**Trigger**: Push to `release/alpha` branch

```bash
# Merge your feature into the alpha branch
git checkout release/alpha
git merge main  # or cherry-pick specific commits
git push origin release/alpha

# 🚀 Pipeline automatically:
# 1. Runs quality checks and tests
# 2. Auto-increments alpha version (0.2.0 → 0.3.0a1 → 0.3.0a2)
# 3. Creates git tag and GitHub release
# 4. Publishes to TestPyPI
```

**Manual trigger with specific version**:
```bash
# Go to Actions → Auto-Release: Alpha → Run workflow
# Enter custom version: 0.4.0a1
```

### 🎯 Beta Release (Feature Testing)

**Trigger**: Push to `release/beta` branch

```bash
# Promote alpha to beta
git checkout release/beta
git merge release/alpha
git push origin release/beta

# 🚀 Pipeline automatically:
# 1. Runs quality checks and tests  
# 2. Auto-increments beta version (0.3.0a5 → 0.3.0b1 → 0.3.0b2)
# 3. Creates git tag and GitHub release
# 4. Publishes to PyPI
```

### 🎯 Release Candidate (Pre-Production)

**Trigger**: Push to `release/rc` branch

```bash
# Promote beta to RC
git checkout release/rc
git merge release/beta
git push origin release/rc

# 🚀 Pipeline automatically:
# 1. Runs quality checks and tests
# 2. Auto-increments RC version (0.3.0b2 → 0.3.0rc1 → 0.3.0rc2)
# 3. Creates git tag and GitHub release
# 4. Publishes to PyPI
```

### 🎉 Stable Release (Production)

**Option 1**: Manual workflow dispatch
```bash
# Go to Actions → Auto-Release: Stable → Run workflow
# Enter stable version: 0.3.0
```

**Option 2**: Direct version update (for experienced users)
```bash
# Manually update version and push to main
git checkout main
git merge release/rc
python scripts/update_version.py 0.3.0
git add pyproject.toml
git commit -m "Release v0.3.0"
git push origin main

# 🚀 Pipeline automatically detects stable version and releases
```

## 🔄 Version Flow Example

Here's how versions progress through the pipeline:

```
0.2.0 (current stable)
    ↓
0.3.0a1 → 0.3.0a2 → 0.3.0a3  (alpha branch → TestPyPI)
    ↓
0.3.0b1 → 0.3.0b2            (beta branch → PyPI)
    ↓  
0.3.0rc1 → 0.3.0rc2          (rc branch → PyPI)
    ↓
0.3.0                        (main branch → PyPI)
```

## 🛠️ Pipeline Features

### ✅ Quality Assurance
- Black code formatting check
- Flake8 linting  
- isort import sorting
- mypy type checking
- Full test suite with 80%+ coverage requirement

### 📦 Automatic Package Management
- Version auto-increment based on current version
- Git tag creation and push
- GitHub release creation with detailed notes
- PyPI/TestPyPI publishing with trusted publishers
- Comprehensive release summaries

### 🎛️ Manual Override Options
- Force specific versions via workflow dispatch
- Skip auto-increment for custom version numbers
- Manual approval gates for production releases

### 📊 Release Documentation
- Auto-generated release notes with installation instructions
- Links to PyPI packages and GitHub releases
- Clear indication of release type (alpha/beta/rc/stable)
- Installation commands for each release type

## 🚨 Troubleshooting

### Pipeline Fails on Quality Checks
```bash
# Fix issues locally first
python -m black .
python -m flake8 .
python -m isort .
python -m mypy src/
python -m pytest

# Then push fix to the release branch
git add .
git commit -m "Fix quality issues"
git push origin release/alpha  # or beta/rc
```

### Version Conflicts
```bash
# Reset release branch to main and restart
git checkout release/alpha
git reset --hard main
git push --force-with-lease origin release/alpha
```

### Publishing Failures
1. Check trusted publisher configuration on PyPI/TestPyPI
2. Verify repository name matches exactly: `cmgrayb/libdyson-rest`
3. Ensure workflow file names match trusted publisher settings
4. Check GitHub environment configuration

### Branch Protection Issues
- Ensure you have admin access to bypass branch protection
- Or create PRs to merge into protected branches
- Use personal access tokens with appropriate permissions

## 💡 Best Practices

1. **Feature Development**: Work on feature branches, merge to main
2. **Alpha Testing**: Merge main into `release/alpha` for early testing
3. **Beta Releases**: Only promote tested alphas to beta
4. **Release Candidates**: Only promote stable betas to RC
5. **Stable Releases**: Only promote thoroughly tested RCs to stable

This automated pipeline eliminates manual version management while maintaining full control over release quality and timing.
