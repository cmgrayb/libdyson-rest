# libdyson-rest

## Python library for interacting with the Dyson REST API

A Python 3 library providing a clean interface for communicating with Dyson devices through their REST API endpoints.

## Disclaimer

I am in no way associated with, paid by, or otherwise related to Dyson or any of its affiliates.

This project is created to further the efforts of others in the community in interacting with the
Dyson devices they have purchased to better integrate them into their smart homes.

At this time, this library is PURELY EXPERIMENTAL and should not be used without carefully examining
the code before doing so. **USE AT YOUR OWN RISK**

## Features

- Clean, intuitive API for Dyson device interaction
- Full type hints support
- Comprehensive error handling
- Async/sync support
- Built-in authentication handling
- Extensive test coverage

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/cmgrayb/libdyson-rest.git
cd libdyson-rest

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

## Quick Start

```python
from libdyson_rest import DysonClient

# Initialize the client
client = DysonClient(
    email="your_email@example.com",
    password="your_password",
    country="US"
)

# Authenticate with Dyson API
client.authenticate()

# Get your devices
devices = client.get_devices()
for device in devices:
    print(f"Device: {device['name']} ({device['serial']})")

# Always close the client when done
client.close()

# Or use as context manager
with DysonClient(email="email@example.com", password="password") as client:
    client.authenticate()
    devices = client.get_devices()
    # Client is automatically closed
```

## Development

This project uses several tools to maintain code quality:

- **Black**: Code formatting (120 character line length)
- **Flake8**: Linting and style checking
- **isort**: Import sorting
- **MyPy**: Type checking
- **Pytest**: Testing framework
- **Pre-commit**: Git hooks

### Setting up Development Environment

1. **Create virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements-dev.txt
   ```

2. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

### VSCode Tasks

This project includes VSCode tasks for common development operations:

- **Setup Dev Environment**: Create venv and install dependencies
- **Format Code**: Run Black formatter
- **Lint Code**: Run Flake8 linter
- **Sort Imports**: Run isort
- **Type Check**: Run MyPy type checker
- **Run Tests**: Execute pytest with coverage
- **Check All**: Run all quality checks in sequence

Access these via `Ctrl+Shift+P` → "Tasks: Run Task"

### Code Quality Commands

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type check
mypy src/libdyson_rest

# Run tests
pytest

# Run all checks
black . && isort . && flake8 . && mypy src/libdyson_rest && pytest
```

### Testing

Run tests with coverage:

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage report
pytest --cov=src/libdyson_rest --cov-report=html
```

## Project Structure

```
libdyson-rest/
├── src/
│   └── libdyson_rest/          # Main library code
│       ├── __init__.py
│       ├── client.py           # Main API client
│       ├── exceptions.py       # Custom exceptions
│       ├── models/             # Data models
│       └── utils/              # Utility functions
├── tests/
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── .vscode/
│   └── tasks.json             # VSCode tasks
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Project configuration
├── .flake8                   # Flake8 configuration
├── .pre-commit-config.yaml   # Pre-commit hooks
└── README.md
```

## Configuration Files

- **pyproject.toml**: Main project configuration (Black, isort, pytest, mypy)
- **.flake8**: Flake8 linting configuration
- **.pre-commit-config.yaml**: Git pre-commit hooks
- **requirements.txt**: Production dependencies
- **requirements-dev.txt**: Development dependencies

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the coding standards
4. Run all quality checks: ensure Black, Flake8, isort, MyPy, and tests pass
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Create a Pull Request

All PRs must pass the full test suite and code quality checks.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

- No hardcoded credentials or sensitive data
- Use environment variables for configuration
- All user inputs are validated
- API responses are sanitized

## Roadmap

- [ ] Complete API endpoint coverage
- [ ] Asynchronous client support
- [ ] WebSocket real-time updates
- [ ] Command-line interface
- [ ] Docker container support
