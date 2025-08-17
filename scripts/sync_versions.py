#!/usr/bin/env python3
"""
Version Synchronization Script for libdyson-rest

This script automates the version synchronization process across:
- .pre-commit-config.yaml
- requirements-dev.txt
- pyproject.toml

Usage:
    python scripts/sync_versions.py [--dry-run] [--verbose]
"""

import argparse
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class VersionSynchronizer:
    """Handles version synchronization across configuration files."""

    def __init__(self, project_root: Path, dry_run: bool = False, verbose: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.verbose = verbose

        # File paths
        self.precommit_config = project_root / ".pre-commit-config.yaml"
        self.requirements_dev = project_root / "requirements-dev.txt"
        self.pyproject_toml = project_root / "pyproject.toml"

    def get_executable_path(self, tool_name: str) -> str:
        """Get the correct executable path for the current platform."""
        is_windows = platform.system() == "Windows"

        if is_windows:
            # Windows: .venv/Scripts/tool.exe
            venv_path = self.project_root / ".venv" / "Scripts" / f"{tool_name}.exe"
        else:
            # Unix/Linux/Mac: .venv/bin/tool
            venv_path = self.project_root / ".venv" / "bin" / tool_name

        # Check if virtual environment executable exists
        if venv_path.exists():
            return str(venv_path)

        # Fallback to system-wide executable (for CI environments)
        if tool_name == "python":
            fallback_path = sys.executable
        else:
            fallback_path = tool_name  # Let the system find it in PATH

        if self.verbose:
            self.log(f"Virtual env path {venv_path} not found, using fallback: {fallback_path}")

        return fallback_path

    def log(self, message: str, force: bool = False) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose or force:
            print(f"[sync_versions] {message}")

    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        if cwd is None:
            cwd = self.project_root

        self.log(f"Running command: {' '.join(command)}")

        if self.dry_run:
            self.log("DRY RUN: Command not executed")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)

        if result.returncode != 0:
            self.log(f"Command failed with code {result.returncode}", force=True)
            self.log(f"STDERR: {result.stderr}", force=True)

        return result

    def update_precommit_versions(self) -> Dict[str, str]:
        """Update pre-commit versions and return the new versions."""
        self.log("Step 1: Updating pre-commit versions...")

        result = self.run_command([self.get_executable_path("pre-commit"), "autoupdate"])

        if result.returncode != 0:
            raise RuntimeError(f"pre-commit autoupdate failed: {result.stderr}")

        # Parse the updated versions from pre-commit config
        return self.parse_precommit_versions()

    def parse_precommit_versions(self) -> Dict[str, str]:
        """Parse tool versions from .pre-commit-config.yaml."""
        versions = {}

        if not self.precommit_config.exists():
            raise FileNotFoundError(f"Pre-commit config not found: {self.precommit_config}")

        content = self.precommit_config.read_text(encoding="utf-8")

        # Tool version patterns
        patterns = {
            "black": r"repo:\s*https://github\.com/psf/black\s*\n\s*rev:\s*([^\s]+)",
            "isort": r"repo:\s*https://github\.com/pycqa/isort\s*\n\s*rev:\s*([^\s]+)",
            "flake8": r"repo:\s*https://github\.com/pycqa/flake8\s*\n\s*rev:\s*([^\s]+)",
            "mypy": r"repo:\s*https://github\.com/pre-commit/mirrors-mypy\s*\n\s*rev:\s*v([^\s]+)",
        }

        for tool, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                version = match.group(1)
                # Remove 'v' prefix for mypy
                if tool == "mypy" and not version.startswith("v"):
                    version = version
                elif tool == "mypy" and version.startswith("v"):
                    version = version[1:]
                versions[tool] = version
                self.log(f"Found {tool} version: {version}")

        return versions

    def get_current_pip_versions(self) -> Dict[str, str]:
        """Get currently installed package versions via pip list."""
        self.log("Getting current pip package versions...")

        result = self.run_command([self.get_executable_path("python"), "-m", "pip", "list", "--format=freeze"])

        if result.returncode != 0:
            raise RuntimeError(f"pip list failed: {result.stderr}")

        versions = {}
        for line in result.stdout.strip().split("\n"):
            if "==" in line:
                package, version = line.split("==", 1)
                package = package.lower().replace("_", "-")
                versions[package] = version

        return versions

    def update_requirements_dev(self, versions: Dict[str, str]) -> None:
        """Update requirements-dev.txt with exact version pins."""
        self.log("Step 2: Updating requirements-dev.txt...")

        if not self.requirements_dev.exists():
            raise FileNotFoundError(f"Requirements file not found: {self.requirements_dev}")

        content = self.requirements_dev.read_text(encoding="utf-8")
        lines = content.strip().split("\n")

        # Get current pip versions to fill in missing ones
        pip_versions = self.get_current_pip_versions()

        # Version mapping from pre-commit to pip package names
        version_mapping = {
            "black": versions.get("black", pip_versions.get("black", "25.1.0")),
            "flake8": versions.get("flake8", pip_versions.get("flake8", "7.3.0")),
            "isort": versions.get("isort", pip_versions.get("isort", "6.0.1")),
            "mypy": versions.get("mypy", pip_versions.get("mypy", "1.17.1")),
            "pytest": pip_versions.get("pytest", "8.4.1"),
            "pytest-cov": pip_versions.get("pytest-cov", "6.2.1"),
            "pre-commit": pip_versions.get("pre-commit", "4.3.0"),
            "types-requests": pip_versions.get("types-requests", "2.32.4.20250809"),
            "types-cryptography": pip_versions.get("types-cryptography", "3.3.23.2"),
            "bandit": pip_versions.get("bandit", "1.8.0"),
        }

        # Update lines to use exact versions
        updated_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                updated_lines.append(line)
                continue

            # Extract package name (handle extras syntax like bandit[toml])
            package_with_extras = re.split(r"[>=<~!]", line)[0].strip()
            package_name = package_with_extras.split("[")[0]  # Remove extras

            if package_name in version_mapping:
                # Preserve extras syntax if present
                if "[" in package_with_extras:
                    new_line = f"{package_with_extras}=={version_mapping[package_name]}"
                else:
                    new_line = f"{package_name}=={version_mapping[package_name]}"
                updated_lines.append(new_line)
                self.log(f"Updated {package_name}: {line} -> {new_line}")
            else:
                updated_lines.append(line)

        new_content = "\n".join(updated_lines) + "\n"

        if self.dry_run:
            self.log("DRY RUN: Would update requirements-dev.txt")
            if self.verbose:
                print("New content would be:")
                print(new_content)
        else:
            self.requirements_dev.write_text(new_content, encoding="utf-8")
            self.log("Updated requirements-dev.txt")

    def update_pyproject_toml(self, versions: Dict[str, str]) -> None:
        """Update pyproject.toml optional dependencies."""
        self.log("Step 3: Updating pyproject.toml...")

        if not self.pyproject_toml.exists():
            raise FileNotFoundError(f"pyproject.toml not found: {self.pyproject_toml}")

        content = self.pyproject_toml.read_text(encoding="utf-8")

        # Get current pip versions
        pip_versions = self.get_current_pip_versions()

        # Build the new dev dependencies section
        version_mapping = {
            "black": versions.get("black", pip_versions.get("black", "25.1.0")),
            "flake8": versions.get("flake8", pip_versions.get("flake8", "7.3.0")),
            "isort": versions.get("isort", pip_versions.get("isort", "6.0.1")),
            "mypy": versions.get("mypy", pip_versions.get("mypy", "1.17.1")),
            "pytest": pip_versions.get("pytest", "8.4.1"),
            "pytest-cov": pip_versions.get("pytest-cov", "6.2.1"),
            "pre-commit": pip_versions.get("pre-commit", "4.3.0"),
            "types-requests": pip_versions.get("types-requests", "2.32.4.20250809"),
            "types-cryptography": pip_versions.get("types-cryptography", "3.3.23.2"),
            "bandit": pip_versions.get("bandit", "1.8.0"),
        }

        new_dev_deps = [
            f'    "black=={version_mapping["black"]}",',
            f'    "flake8=={version_mapping["flake8"]}",',
            f'    "isort=={version_mapping["isort"]}",',
            f'    "pytest=={version_mapping["pytest"]}",',
            f'    "pytest-cov=={version_mapping["pytest-cov"]}",',
            f'    "pre-commit=={version_mapping["pre-commit"]}",',
            f'    "mypy=={version_mapping["mypy"]}",',
            f'    "types-requests=={version_mapping["types-requests"]}",',
            f'    "types-cryptography=={version_mapping["types-cryptography"]}",',
            f'    "bandit[toml]=={version_mapping["bandit"]}",',
        ]

        # Pattern to match the dev dependencies section
        pattern = r"(\[project\.optional-dependencies\]\s*\ndev\s*=\s*\[)(.*?)(\])"

        def replace_dev_deps(match: re.Match[str]) -> str:
            return match.group(1) + "\n" + "\n".join(new_dev_deps) + "\n" + match.group(3)

        new_content = re.sub(pattern, replace_dev_deps, content, flags=re.DOTALL)

        if self.dry_run:
            self.log("DRY RUN: Would update pyproject.toml")
            if self.verbose:
                print("New dev dependencies section would be:")
                for dep in new_dev_deps:
                    print(dep)
        else:
            self.pyproject_toml.write_text(new_content, encoding="utf-8")
            self.log("Updated pyproject.toml")

    def install_updated_dependencies(self) -> None:
        """Install the updated dependencies."""
        self.log("Step 4: Installing updated dependencies...")

        result = self.run_command(
            [
                self.get_executable_path("python"),
                "-m",
                "pip",
                "install",
                "-r",
                "requirements-dev.txt",
            ]
        )

        if result.returncode != 0:
            raise RuntimeError(f"pip install failed: {result.stderr}")

        self.log("Dependencies installed successfully")

    def verify_tools(self) -> bool:
        """Verify all tools work correctly."""
        self.log("Step 5: Verifying tools...")

        checks = [
            (
                [self.get_executable_path("python"), "-m", "black", "--check", "."],
                "Black formatting",
            ),
            ([self.get_executable_path("python"), "-m", "flake8", "."], "Flake8 linting"),
            (
                [self.get_executable_path("python"), "-m", "isort", "--check-only", "."],
                "isort import sorting",
            ),
            ([self.get_executable_path("python"), "-m", "mypy", "src/"], "mypy type checking"),
        ]

        all_passed = True

        for command, description in checks:
            result = self.run_command(command)
            if result.returncode == 0:
                self.log(f"✓ {description} passed")
            else:
                self.log(f"✗ {description} failed", force=True)
                all_passed = False

        return all_passed

    def run_precommit_verification(self) -> bool:
        """Run pre-commit hooks to verify everything works."""
        self.log("Step 6: Running pre-commit verification...")

        result = self.run_command([self.get_executable_path("pre-commit"), "run", "--all-files"])

        if result.returncode == 0:
            self.log("✓ Pre-commit hooks passed")
            return True
        else:
            self.log("✗ Pre-commit hooks failed", force=True)
            return False

    def synchronize(self) -> bool:
        """Run the complete synchronization process."""
        self.log("Starting version synchronization process...", force=True)

        try:
            # Step 1: Update pre-commit versions
            versions = self.update_precommit_versions()

            # Step 2: Update requirements-dev.txt
            self.update_requirements_dev(versions)

            # Step 3: Update pyproject.toml
            self.update_pyproject_toml(versions)

            # Step 4: Install updated dependencies
            self.install_updated_dependencies()

            # Step 5: Verify tools work
            tools_ok = self.verify_tools()

            # Step 6: Verify pre-commit hooks
            precommit_ok = self.run_precommit_verification()

            if tools_ok and precommit_ok:
                self.log("✓ Version synchronization completed successfully!", force=True)
                return True
            else:
                self.log("✗ Version synchronization completed with errors", force=True)
                return False

        except Exception as e:
            self.log(f"✗ Version synchronization failed: {e}", force=True)
            return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Synchronize tool versions across configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script automates the version synchronization process by:
1. Running 'pre-commit autoupdate' to get latest versions
2. Updating requirements-dev.txt with exact version pins
3. Updating pyproject.toml optional dependencies
4. Installing updated dependencies
5. Verifying all tools work correctly
6. Running pre-commit hooks for final verification
        """,
    )

    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Find project root (directory containing .pre-commit-config.yaml)
    project_root = Path.cwd()
    while project_root != project_root.parent:
        if (project_root / ".pre-commit-config.yaml").exists():
            break
        project_root = project_root.parent
    else:
        print("Error: Could not find project root (.pre-commit-config.yaml not found)")
        return 1

    # Initialize synchronizer
    synchronizer = VersionSynchronizer(project_root=project_root, dry_run=args.dry_run, verbose=args.verbose)

    # Run synchronization
    success = synchronizer.synchronize()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
