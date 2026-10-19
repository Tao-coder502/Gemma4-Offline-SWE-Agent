"""
tests/test_evaluator.py
=======================
Validates the TestRunnerEvaluator output parsing, dual-tuple unpacking,
and error signature extraction.
"""

from tools.test_runner_evaluator import evaluate_test_outcome, TestOutcome


def test_evaluator_tuple_unpacking():
    # 1. Test passing output
    pytest_pass = "==== 1 passed in 0.05s ===="
    passed, msg = evaluate_test_outcome(command="pytest test_app.py", output=pytest_pass, returncode=0)
    assert passed is True
    assert "passed 1 tests cleanly" in msg

    # Also verify TestOutcome named attributes
    outcome = evaluate_test_outcome(command="pytest test_app.py", output=pytest_pass, returncode=0)
    assert isinstance(outcome, tuple)
    assert outcome.passed is True
    assert outcome.error_signature is None


def test_evaluator_failure_signature():
    pytest_fail = """
=================================== FAILURES ===================================
__________________________________ test_error __________________________________
    def test_error():
>       raise ValueError("Invalid blueprint name with dots.")
E       ValueError: Invalid blueprint name with dots.
=========================== short test summary info ===========================
FAILED test_blueprint.py::test_error - ValueError: Invalid blueprint name with dots.
============================== 1 failed in 0.12s ===============================
"""
    passed, summary = evaluate_test_outcome(command="pytest test_app.py", output=pytest_fail, returncode=1)
    assert passed is False
    assert "failed with 1 test failures" in summary

    outcome = evaluate_test_outcome(command="pytest test_app.py", output=pytest_fail, returncode=1)
    assert outcome.passed is False
    assert "ValueError" in str(outcome.error_signature)
