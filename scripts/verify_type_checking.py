#!/usr/bin/env python3
"""
Script to verify strict type checking implementation.

This script demonstrates that the libdyson-rest library now has comprehensive
type checking and will catch common type-related errors at development time.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report results."""
    print(f"\n🔍 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("❌ FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main() -> None:
    """Main verification script."""
    print("🚀 Verifying Strict Type Checking Implementation")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ ERROR: Must run from project root directory")
        sys.exit(1)

    # Tests to run
    tests = [
        {
            "cmd": [".venv/Scripts/python.exe", "-m", "mypy", "src/libdyson_rest"],
            "description": "Basic mypy type checking",
        },
        {
            "cmd": [".venv/Scripts/python.exe", "-m", "mypy", "src/libdyson_rest", "--strict"],
            "description": "Strict mypy type checking",
        },
        {"cmd": [".venv/Scripts/python.exe", "-m", "pytest", "-v"], "description": "Unit and integration tests"},
        {"cmd": [".venv/Scripts/python.exe", "-m", "flake8", "."], "description": "Code style linting"},
        {"cmd": [".venv/Scripts/python.exe", "-m", "black", "--check", "."], "description": "Code formatting check"},
    ]

    results = []
    for test in tests:
        success = run_command(test["cmd"], test["description"])
        results.append(success)

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 ALL CHECKS PASSED! Strict type checking is working correctly.")
        print("\n✨ Your library now has:")
        print("   • Comprehensive type annotations")
        print("   • Strict mypy configuration")
        print("   • Runtime type safety")
        print("   • Enhanced IDE support")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} checks failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
