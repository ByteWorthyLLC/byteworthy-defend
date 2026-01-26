"""Test runner script for HifzDefend.

Provides convenient commands for running different test suites:
- Unit tests only (fast)
- Integration tests
- Performance benchmarks
- False positive tests
- Full test suite with coverage

Usage:
    python scripts/run_tests.py unit          # Run unit tests only
    python scripts/run_tests.py integration   # Run integration tests
    python scripts/run_tests.py benchmarks    # Run performance benchmarks
    python scripts/run_tests.py false-pos     # Run false positive tests
    python scripts/run_tests.py all           # Run all tests
    python scripts/run_tests.py coverage      # Run tests with coverage report
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run command and return exit code."""
    print(f"\n{'='*80}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*80}\n")

    result = subprocess.run(cmd)
    return result.returncode


def run_unit_tests():
    """Run unit tests only (fast)."""
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "-m", "not slow and not benchmark and not integration",
        "--tb=short",
    ]
    return run_command(cmd)


def run_integration_tests():
    """Run integration tests."""
    cmd = [
        "pytest",
        "tests/test_integration/",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd)


def run_benchmark_tests():
    """Run performance benchmarks."""
    cmd = [
        "pytest",
        "tests/benchmarks/test_performance.py",
        "-v",
        "-s",  # Show print output for benchmark results
        "--tb=short",
    ]
    return run_command(cmd)


def run_false_positive_tests():
    """Run false positive rate tests."""
    cmd = [
        "pytest",
        "tests/benchmarks/test_false_positives.py",
        "-v",
        "-s",
        "--tb=short",
    ]
    return run_command(cmd)


def run_all_tests():
    """Run all tests."""
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd)


def run_coverage():
    """Run tests with coverage report."""
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--cov=src/hifzdefend",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--tb=short",
    ]
    exit_code = run_command(cmd)

    if exit_code == 0:
        print("\n" + "="*80)
        print("Coverage report generated in htmlcov/index.html")
        print("="*80)

    return exit_code


def run_specific_test(test_path: str):
    """Run specific test file or test."""
    cmd = [
        "pytest",
        test_path,
        "-v",
        "-s",
        "--tb=short",
    ]
    return run_command(cmd)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    test_type = sys.argv[1].lower()

    if test_type == "unit":
        return run_unit_tests()
    elif test_type == "integration":
        return run_integration_tests()
    elif test_type == "benchmarks" or test_type == "perf":
        return run_benchmark_tests()
    elif test_type == "false-pos" or test_type == "fp":
        return run_false_positive_tests()
    elif test_type == "all":
        return run_all_tests()
    elif test_type == "coverage" or test_type == "cov":
        return run_coverage()
    elif test_type.startswith("tests/"):
        # Run specific test file
        return run_specific_test(test_type)
    else:
        print(f"Unknown test type: {test_type}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
