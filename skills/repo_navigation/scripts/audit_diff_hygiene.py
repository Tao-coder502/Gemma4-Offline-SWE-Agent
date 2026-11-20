#!/usr/bin/env python3
"""
Audits current git diff for SWE-bench hygiene compliance.
Usage: python audit_diff_hygiene.py [workspace_dir]
"""

import sys
import subprocess
from pathlib import Path

def audit_diff(workspace: Path) -> bool:
    try:
        # Check modified files
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=True
        )
        files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except Exception as e:
        print(f"[AUDIT FAIL] Failed to inspect git status: {e}")
        return False

    if not files:
        print("[AUDIT WARN] Git diff is completely empty. No changes detected.")
        return False

    violations = []
    for f in files:
        f_lower = f.lower()
        if f_lower.startswith("tests/") or f_lower.startswith("test/") or "/test_" in f_lower or f_lower.startswith("test_"):
            violations.append(f"CRITICAL: Test file modified: {f}")
        if f_lower.endswith((".pyc", ".pyo", ".pyd", ".so", ".bin")):
            violations.append(f"CRITICAL: Compiled/binary artifact modified: {f}")

    # Inspect total line changes
    try:
        stat_res = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        print("[Diff Summary]")
        print(stat_res.stdout.strip())
    except Exception:
        pass

    if violations:
        for v in violations:
            print(f"[AUDIT VIOLATION] {v}")
        return False

    print(f"[AUDIT PASS] Clean patch! {len(files)} file(s) modified, 0 test files touched.")
    return True

if __name__ == "__main__":
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    if not ws.exists():
        ws = Path(".")
    ok = audit_diff(ws)
    sys.exit(0 if ok else 1)
