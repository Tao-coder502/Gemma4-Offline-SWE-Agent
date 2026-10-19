#!/usr/bin/env python3
"""
tools/test_runner_evaluator.py
==============================
Adaptive Test Outcome Evaluator for Gemma 4 SWE Agent.

Supports:
  1. pytest (exact passed/failed counts, exit codes)
  2. python -m unittest (OK vs FAILED)
  3. Custom test scripts (exit code 0, absence of tracebacks)
  4. Precise error signature extraction for the Test-Driven Repair loop.
"""

from __future__ import annotations

import re
from typing import Tuple, Optional


class TestOutcome(tuple):
    """
    Dual-compatible outcome tuple: unpacks cleanly as 2-tuple (passed, summary)
    while exposing .passed, .summary, and .error_signature attributes.
    """
    passed: bool
    summary: str
    error_signature: Optional[str]

    def __new__(cls, passed: bool, summary: str, error_signature: Optional[str] = None):
        inst = super().__new__(cls, (passed, summary))
        inst.passed = passed
        inst.summary = summary
        inst.error_signature = error_signature
        return inst


def evaluate_test_outcome(
    command: str,
    output: str,
    returncode: int,
    pass_regex: Optional[str] = None
) -> TestOutcome:
    """
    Evaluates whether a test run passed, and extracts diagnostic summary and error signature.
    Returns TestOutcome which unpacks cleanly as (passed: bool, summary: str).
    """
    # 1. If explicit pass_regex is provided in benchmark metadata
    if pass_regex:
        if re.search(pass_regex, output, re.IGNORECASE):
            # Check for conflicting failure signals (e.g. "1 failed, 2 passed")
            if "failed" in output.lower() and "passed" in output.lower():
                failed_match = re.search(r"(\d+)\s+failed", output)
                if failed_match and int(failed_match.group(1)) > 0:
                    return TestOutcome(False, f"Partial pass with {failed_match.group(1)} failures", _extract_error(output))
            return TestOutcome(True, "Passed via regex match", None)

    # 2. Pytest Detection
    if "pytest" in command or "passed in " in output or "failed in " in output:
        # e.g. "5 passed in 0.23s"
        pass_m = re.search(r"(\d+)\s+passed", output)
        fail_m = re.search(r"(\d+)\s+failed", output)
        err_m = re.search(r"(\d+)\s+error", output)

        if fail_m and int(fail_m.group(1)) > 0:
            return TestOutcome(False, f"pytest failed with {fail_m.group(1)} test failures", _extract_error(output))
        if err_m and int(err_m.group(1)) > 0:
            return TestOutcome(False, f"pytest encountered {err_m.group(1)} errors", _extract_error(output))
        if pass_m and int(pass_m.group(1)) > 0 and returncode == 0:
            return TestOutcome(True, f"pytest passed {pass_m.group(1)} tests cleanly", None)

    # 3. Unittest Detection
    if "unittest" in command or "Ran " in output:
        # e.g. "Ran 12 tests in 0.045s\n\nOK"
        if re.search(r"\bOK\b", output) and returncode == 0:
            return TestOutcome(True, "unittest suite passed (OK)", None)
        if "FAILED (" in output:
            return TestOutcome(False, "unittest suite failed", _extract_error(output))

    # 4. Standard exit code & exception heuristic
    if returncode == 0:
        if not any(indicator in output for indicator in ["Traceback (most recent call last)", "SyntaxError:", "ImportError:"]):
            return TestOutcome(True, "Command exited with code 0 without unhandled exceptions", None)
        else:
            return TestOutcome(False, "Command exited 0 but emitted unhandled traceback", _extract_error(output))

    return TestOutcome(False, f"Command exited with non-zero returncode {returncode}", _extract_error(output))


def _extract_error(output: str) -> Optional[str]:
    """Extracts the immediate failing exception or assertion message."""
    lines = output.splitlines()
    for line in reversed(lines):
        line = line.strip()
        # Look for standard Python exception patterns
        if re.match(r"^[A-Z]\w*(?:Error|Exception|Warning):\s*.+", line):
            return line
        if line.startswith("FAILED "):
            return line
    return None
