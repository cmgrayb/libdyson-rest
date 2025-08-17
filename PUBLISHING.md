# Publishing Guide

This document explains how to publish `libdyson-rest` to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both [TestPyPI](https://test.pypi.org/) and [PyPI](https://pypi.org/)
2. **API Tokens**: Generate API tokens for both platforms
3. **Repository Secrets**: Add tokens to GitHub repository secrets

## GitHub Actions Publishing

The recommended way to publish is through GitHub Actions, which provides automated publishing with proper CI/CD practices.

### Setup Repository Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `TESTPYPI_API_TOKEN`: Your TestPyPI API token
- `PYPI_API_TOKEN`: Your PyPI API token

### Publishing Process

#### Test Publishing (TestPyPI)

1. **Manual Trigger**: Go to Actions → Publish to PyPI → Run workflow
   - Choose "testpypi" as the environment
   - This uploads to TestPyPI for testing

2. **Verify Installation**:
   ```bash
   pip install -i https://test.pypi.org/simple/ libdyson-rest
   ```

#### Production Publishing (PyPI)

1. **Create a Release**: Tag a new release on GitHub
   - Format: `v0.2.0` (semver)
   - This automatically triggers production publishing

2. **Manual Trigger**: Alternatively, use workflow dispatch
   - Choose "pypi" as the environment
   - Only use for hotfixes or special cases

## Local Publishing (Development)

For development and testing, you can publish locally using the provided script:

### Test Publishing
```bash
python .github/scripts/publish_to_pypi.py --test
```

### Production Publishing
```bash
python .github/scripts/publish_to_pypi.py --prod
```

### Build and Check Only
```bash
python .github/scripts/publish_to_pypi.py --check
```

## Quality Checks

The publishing process includes automatic quality checks:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Code linting
- **Package validation**: Metadata and structure checks

## Version Management

Update version in `pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

Follow [semantic versioning](https://semver.org/):
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

## Package Structure

The built package includes:
- Source code (`src/libdyson_rest/`)
- Documentation (`README.md`, `LICENSE`)
- Metadata (`pyproject.toml`)
- Examples (excluded from distribution)

## Troubleshooting

### Common Issues

1. **Token Authentication**: Ensure API tokens are correctly set
2. **Version Conflicts**: Check if version already exists on PyPI
3. **Quality Checks**: Fix formatting and linting issues
4. **Dependencies**: Ensure all dependencies are properly declared

### Manual Package Check
```bash
python -m twine check dist/*
```

### View Package Contents
```bash
python -m zipfile -l dist/libdyson_rest-*.whl
```

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` (if exists)
- [ ] Run quality checks locally
- [ ] Test package build (`python .github/scripts/publish_to_pypi.py --check`)
- [ ] Test on TestPyPI first
- [ ] Create GitHub release with proper tags
- [ ] Verify PyPI upload
- [ ] Test installation from PyPI
