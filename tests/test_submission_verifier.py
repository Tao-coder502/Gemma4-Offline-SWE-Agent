"""
tests/test_submission_verifier.py
==================================
Runs the full 81-check clean-room submission verifier against submission.zip
to guarantee zero regressions on Google ADK schema, secrets, budgets, and offline discipline.
"""

from pathlib import Path
from tools.verify_clean_submission import CleanVerificationSuite

ROOT = Path(__file__).resolve().parent.parent


def test_clean_room_submission_verification():
    zip_path = ROOT / "submission.zip"
    assert zip_path.exists(), "submission.zip must exist prior to verification"
    
    suite = CleanVerificationSuite(root=ROOT, zip_path=zip_path)
    success = suite.run_all_checks()
    
    assert success is True, f"Submission verification failed with {suite.failed} failures"
    assert suite.failed == 0
    assert suite.passed >= 80
