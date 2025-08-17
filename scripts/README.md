# Development Scripts

This directory contains utility scripts for maintaining the libdyson-rest development environment.

## sync_versions.py

Automated version synchronization script that keeps all development tool versions consistent across configuration files.

### Purpose
Maintains version alignment across:
- `.pre-commit-config.yaml` - Pre-commit hook versions
- `requirements-dev.txt` - Python package versions for local development
- `pyproject.toml` - Optional dependencies for package consumers

### Usage

```bash
# Preview changes without making modifications
python scripts/sync_versions.py --dry-run --verbose

# Execute full synchronization process
python scripts/sync_versions.py --verbose

# Quiet mode (errors and results only)
python scripts/sync_versions.py
```

### Process Steps
1. **Update Pre-commit**: Runs `pre-commit autoupdate` to get latest hook versions
2. **Sync requirements-dev.txt**: Updates to exact version pins matching pre-commit
3. **Sync pyproject.toml**: Updates optional dependencies to match requirements-dev.txt
4. **Install Dependencies**: Installs updated packages in virtual environment
5. **Verify Tools**: Tests all quality tools work correctly
6. **Verify Pre-commit**: Runs all pre-commit hooks as final validation

### VSCode Integration
Available as VSCode tasks via Ctrl+Shift+P → "Tasks: Run Task":
- **Sync Tool Versions (Dry Run)**: Preview changes
- **Sync Tool Versions (Python)**: Execute synchronization

### Benefits
- **Consistency**: Eliminates version conflicts between environments
- **Automation**: Reduces manual maintenance overhead
- **Safety**: Dry-run mode and validation prevent broken configurations
- **Transparency**: Verbose logging shows exactly what changes are made

### When to Use
- After updating any development tool manually
- When pre-commit hooks fail due to version mismatches
- During periodic maintenance to keep tools current
- Before major releases to ensure consistent tool versions
