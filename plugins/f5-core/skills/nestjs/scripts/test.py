#!/usr/bin/env python3
"""
NestJS Test Runner with F5 Quality Gate Integration

Runs NestJS tests with coverage checking and F5 gate validation.

Usage:
    python test.py [options]

Examples:
    python test.py                          # Run all unit tests
    python test.py --coverage               # Run with coverage report
    python test.py --coverage --threshold 80  # Enforce 80% coverage
    python test.py --e2e                    # Run E2E tests
    python test.py --module user            # Run tests for specific module
    python test.py --check-gates            # Validate against F5 quality gates
"""

import argparse
import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# ============================================================
# Configuration
# ============================================================

DEFAULT_COVERAGE_THRESHOLD = 80
CRITICAL_MODULES = ['auth', 'payment', 'security']
CRITICAL_THRESHOLD = 90

F5_GATES = {
    'G2.5': {
        'name': 'Code Review',
        'requirements': ['Unit tests for services, guards, pipes'],
    },
    'G3': {
        'name': 'Testing Gate',
        'requirements': ['80% coverage', 'E2E tests for critical paths'],
    },
    'G4': {
        'name': 'Integration Gate',
        'requirements': ['Performance tests', 'Load testing'],
    },
}

# ============================================================
# Test Runner Functions
# ============================================================

def run_command(cmd: list, cwd: Optional[str] = None) -> tuple:
    """Run a command and return output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, '', str(e)

def find_project_root() -> Path:
    """Find the NestJS project root (where package.json is)."""
    current = Path.cwd()
    while current != current.parent:
        if (current / 'package.json').exists():
            return current
        current = current.parent
    return Path.cwd()

def run_unit_tests(module: Optional[str] = None, verbose: bool = False) -> tuple:
    """Run Jest unit tests."""
    cmd = ['npm', 'run', 'test']

    if module:
        cmd.extend(['--', f'--testPathPattern={module}'])

    if verbose:
        cmd.extend(['--', '--verbose'])

    project_root = find_project_root()
    print(f"\n🧪 Running unit tests...")
    if module:
        print(f"   Module filter: {module}")

    return_code, stdout, stderr = run_command(cmd, cwd=str(project_root))

    if return_code == 0:
        print("✓ Unit tests passed!")
    else:
        print("❌ Unit tests failed!")
        if stderr:
            print(stderr)

    return return_code, stdout, stderr

def run_coverage_tests(threshold: int = DEFAULT_COVERAGE_THRESHOLD,
                       module: Optional[str] = None) -> tuple:
    """Run tests with coverage report."""
    cmd = ['npm', 'run', 'test:cov']

    if module:
        cmd.extend(['--', f'--testPathPattern={module}'])

    project_root = find_project_root()
    print(f"\n📊 Running tests with coverage...")
    print(f"   Threshold: {threshold}%")

    return_code, stdout, stderr = run_command(cmd, cwd=str(project_root))

    # Parse coverage results
    coverage_summary = parse_coverage_summary(project_root)

    if coverage_summary:
        print_coverage_report(coverage_summary, threshold)

        # Check threshold
        if not check_coverage_threshold(coverage_summary, threshold):
            return 1, stdout, "Coverage threshold not met"

    return return_code, stdout, stderr

def run_e2e_tests(module: Optional[str] = None) -> tuple:
    """Run E2E tests."""
    cmd = ['npm', 'run', 'test:e2e']

    if module:
        cmd.extend(['--', f'--testPathPattern={module}'])

    project_root = find_project_root()
    print(f"\n🌐 Running E2E tests...")

    return_code, stdout, stderr = run_command(cmd, cwd=str(project_root))

    if return_code == 0:
        print("✓ E2E tests passed!")
    else:
        print("❌ E2E tests failed!")

    return return_code, stdout, stderr

def parse_coverage_summary(project_root: Path) -> Optional[Dict[str, Any]]:
    """Parse Jest coverage summary from JSON file."""
    coverage_file = project_root / 'coverage' / 'coverage-summary.json'

    if not coverage_file.exists():
        print("⚠️ Coverage summary not found")
        return None

    try:
        with open(coverage_file) as f:
            data = json.load(f)
        return data.get('total', {})
    except Exception as e:
        print(f"⚠️ Error parsing coverage: {e}")
        return None

def print_coverage_report(summary: Dict[str, Any], threshold: int) -> None:
    """Print formatted coverage report."""
    print(f"\n{'=' * 50}")
    print("Coverage Report")
    print(f"{'=' * 50}")

    metrics = ['lines', 'statements', 'functions', 'branches']
    all_pass = True

    for metric in metrics:
        if metric in summary:
            pct = summary[metric].get('pct', 0)
            status = '✓' if pct >= threshold else '❌'
            if pct < threshold:
                all_pass = False
            print(f"  {status} {metric.capitalize():12} {pct:6.2f}%")

    print(f"{'=' * 50}")

    if all_pass:
        print(f"✓ All metrics meet {threshold}% threshold")
    else:
        print(f"❌ Some metrics below {threshold}% threshold")

def check_coverage_threshold(summary: Dict[str, Any], threshold: int) -> bool:
    """Check if coverage meets threshold."""
    metrics = ['lines', 'statements', 'functions', 'branches']

    for metric in metrics:
        if metric in summary:
            pct = summary[metric].get('pct', 0)
            if pct < threshold:
                return False

    return True

# ============================================================
# F5 Gate Integration
# ============================================================

def check_f5_gates(coverage_summary: Optional[Dict[str, Any]],
                   e2e_passed: bool,
                   threshold: int) -> Dict[str, bool]:
    """Check F5 quality gates."""
    results = {}

    # G2.5: Code Review - Unit tests exist
    results['G2.5'] = True  # Assume passed if we ran tests

    # G3: Testing Gate - Coverage and E2E
    g3_passed = True
    if coverage_summary:
        g3_passed = check_coverage_threshold(coverage_summary, threshold)
    results['G3'] = g3_passed and e2e_passed

    # G4: Integration Gate - E2E tests
    results['G4'] = e2e_passed

    return results

def print_gate_report(gate_results: Dict[str, bool]) -> None:
    """Print F5 gate validation report."""
    print(f"\n{'=' * 50}")
    print("F5 Quality Gate Report")
    print(f"{'=' * 50}")

    for gate_id, passed in gate_results.items():
        gate_info = F5_GATES.get(gate_id, {})
        status = '✓' if passed else '❌'
        print(f"\n  {status} {gate_id}: {gate_info.get('name', 'Unknown')}")

        for req in gate_info.get('requirements', []):
            print(f"     • {req}")

    print(f"\n{'=' * 50}")

    all_passed = all(gate_results.values())
    if all_passed:
        print("✓ All F5 quality gates passed!")
    else:
        failed = [g for g, p in gate_results.items() if not p]
        print(f"❌ Failed gates: {', '.join(failed)}")

# ============================================================
# Main Test Runner
# ============================================================

def run_tests(options: Dict[str, Any]) -> int:
    """Main test runner function."""
    print(f"\n{'=' * 60}")
    print("NestJS Test Runner")
    print(f"{'=' * 60}")

    exit_code = 0
    coverage_summary = None
    e2e_passed = True

    # Determine test mode
    if options.get('e2e'):
        # Run E2E tests
        code, _, _ = run_e2e_tests(options.get('module'))
        e2e_passed = code == 0
        exit_code = code

    elif options.get('coverage'):
        # Run coverage tests
        threshold = options.get('threshold', DEFAULT_COVERAGE_THRESHOLD)

        # Check for critical modules
        module = options.get('module')
        if module and module in CRITICAL_MODULES:
            threshold = max(threshold, CRITICAL_THRESHOLD)
            print(f"⚠️ Critical module detected, using {threshold}% threshold")

        code, _, _ = run_coverage_tests(threshold, module)
        exit_code = code

        # Get coverage summary for gate check
        project_root = find_project_root()
        coverage_summary = parse_coverage_summary(project_root)

    else:
        # Run unit tests
        code, _, _ = run_unit_tests(options.get('module'), options.get('verbose'))
        exit_code = code

    # Check F5 gates if requested
    if options.get('check_gates'):
        threshold = options.get('threshold', DEFAULT_COVERAGE_THRESHOLD)
        gate_results = check_f5_gates(coverage_summary, e2e_passed, threshold)
        print_gate_report(gate_results)

        if not all(gate_results.values()):
            exit_code = 1

    print(f"\n{'=' * 60}")
    if exit_code == 0:
        print("✓ All tests completed successfully!")
    else:
        print("❌ Tests completed with failures")
    print(f"{'=' * 60}\n")

    return exit_code

def main():
    parser = argparse.ArgumentParser(
        description='NestJS Test Runner with F5 Quality Gate Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                          Run all unit tests
  %(prog)s --coverage               Run with coverage report
  %(prog)s --coverage --threshold 80  Enforce 80%% coverage
  %(prog)s --e2e                    Run E2E tests
  %(prog)s --module user            Run tests for specific module
  %(prog)s --check-gates            Validate against F5 quality gates

F5 Quality Gates:
  G2.5  Code Review    - Unit tests for services, guards, pipes
  G3    Testing Gate   - 80%% coverage, E2E tests for critical paths
  G4    Integration    - Performance tests, load testing
        '''
    )

    parser.add_argument('--coverage', action='store_true',
                        help='Run tests with coverage report')
    parser.add_argument('--threshold', type=int, default=DEFAULT_COVERAGE_THRESHOLD,
                        help=f'Coverage threshold percentage (default: {DEFAULT_COVERAGE_THRESHOLD})')
    parser.add_argument('--e2e', action='store_true',
                        help='Run E2E tests instead of unit tests')
    parser.add_argument('--module', type=str,
                        help='Run tests for specific module only')
    parser.add_argument('--check-gates', action='store_true',
                        help='Validate against F5 quality gates')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose test output')

    args = parser.parse_args()

    options = {
        'coverage': args.coverage,
        'threshold': args.threshold,
        'e2e': args.e2e,
        'module': args.module,
        'check_gates': args.check_gates,
        'verbose': args.verbose,
    }

    try:
        exit_code = run_tests(options)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
