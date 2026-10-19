#!/usr/bin/env python3
"""
tools/sandbox.py
================
Enterprise-Hardened Tool Sandbox & SAST Patch Security Auditor.
Provides defense-in-depth host containment and static security analysis:
  1. PathJail: Strict path canonicalization preventing directory traversal escapes.
  2. CommandSanitizer: Intercepts and blocks destructive host commands & network tools.
  3. PatchSecurityAuditor: Lightweight AST & pattern-based SAST scanning on proposed diffs.
  4. ToolSandbox: Unified executor exposing all 9 ADK tools within bounded budgets.
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


class SecurityJailViolation(Exception):
    """Raised when an operation attempts to escape the designated workspace boundary."""
    pass


class CommandSecurityViolation(Exception):
    """Raised when a forbidden or destructive shell command is attempted."""
    pass


class SASTSecurityViolation(Exception):
    """Raised when a proposed patch introduces malicious or high-risk code patterns."""
    pass


# ---------------------------------------------------------------------------
# 1. Path Jail Guard
# ---------------------------------------------------------------------------
class PathJail:
    """Strictly jails filesystem operations within the workspace or approved scratch paths."""

    def __init__(self, workspace: Path, allowed_scratch: Optional[Path] = None):
        self.workspace = workspace.resolve()
        # Restrict allowed scratch strictly to /tmp or explicitly passed directory
        self.allowed_scratch = allowed_scratch.resolve() if allowed_scratch is not None else Path("/tmp").resolve()

    def validate_read_path(self, target: str | Path) -> Path:
        """Ensures file to read resides inside the workspace or approved scratch directory."""
        raw_path = Path(target)
        resolved = (self.workspace / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()
        
        # Check if contained in workspace or scratch
        in_workspace = resolved == self.workspace or resolved.is_relative_to(self.workspace)
        in_scratch = resolved == self.allowed_scratch or resolved.is_relative_to(self.allowed_scratch)

        if not (in_workspace or in_scratch):
            raise SecurityJailViolation(
                f"Path jail violation: '{target}' resolves to '{resolved}', which is outside the workspace."
            )
        return resolved

    def validate_write_path(self, target: str | Path, allow_scratch: bool = True) -> Path:
        """Ensures file to write/edit resides strictly within workspace or scratch directory."""
        raw_path = Path(target)
        resolved = (self.workspace / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()

        in_workspace = resolved == self.workspace or resolved.is_relative_to(self.workspace)
        in_scratch = allow_scratch and (resolved == self.allowed_scratch or resolved.is_relative_to(self.allowed_scratch))

        if not (in_workspace or in_scratch):
            raise SecurityJailViolation(
                f"Path jail violation: Write target '{target}' outside workspace boundary: '{resolved}'."
            )
        return resolved


# ---------------------------------------------------------------------------
# 2. Command Sanitizer Guard
# ---------------------------------------------------------------------------
class CommandSanitizer:
    """Interprets and sanitizes shell commands to prevent host destruction and network escapes."""

    # High-risk destructive commands outside sandboxed containers
    DESTRUCTIVE_PATTERNS = [
        re.compile(r"\brm\s+-(?:r[fF]|fr)\s+/(?:\s|$)", re.IGNORECASE),
        re.compile(r"\brm\s+-(?:r[fF]|fr)\s+/\*", re.IGNORECASE),
        re.compile(r"\bmkfs(?:\.[a-z0-9]+)?\b", re.IGNORECASE),
        re.compile(r"\bdd\s+if=.*of=/dev/(?:sd[a-z]|nvme|hd[a-z]|null|zero)", re.IGNORECASE),
        re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", re.IGNORECASE),  # Fork bomb
        re.compile(r">\s*/dev/(?:sd[a-z]|nvme[0-9]n[0-9])", re.IGNORECASE),
    ]

    # Offline air-gap enforcement patterns
    FORBIDDEN_NETWORK_TOOLS = [
        re.compile(r"\b(?:nc|ncat|netcat)\s+.*-e\b", re.IGNORECASE),
        re.compile(r"\b(?:curl|wget|fetch|lynx)\s+https?://", re.IGNORECASE),
        re.compile(r"\b(?:telnet|ftp|ssh|scp|sftp|rsync)\s+", re.IGNORECASE),
        re.compile(r"\bpython(?:3)?\s+-m\s+http\.server\b", re.IGNORECASE),
    ]

    @classmethod
    def sanitize(cls, command: str) -> None:
        """Validates command against destructive and unauthorized networking patterns."""
        cmd_strip = command.strip()
        for pat in cls.DESTRUCTIVE_PATTERNS:
            if pat.search(cmd_strip):
                raise CommandSecurityViolation(f"Blocked destructive command pattern in: {command}")

        for net_pat in cls.FORBIDDEN_NETWORK_TOOLS:
            if net_pat.search(cmd_strip):
                raise CommandSecurityViolation(
                    f"Blocked unauthorized network / exfiltration command in air-gapped mode: {command}"
                )


# ---------------------------------------------------------------------------
# 3. SAST Patch Security Auditor
# ---------------------------------------------------------------------------
class PatchSecurityAuditor:
    """Lightweight Static Application Security Testing (SAST) for proposed patches."""

    # Dangerous functions and execution primitives
    DANGEROUS_CALLS = {
        "eval", "exec", "__import__", "compile",
    }

    # High-risk patterns in diff text
    RISKY_PATTERNS = [
        (re.compile(r"\b(?:eval|exec)\s*\("), "Forbidden execution primitive eval/exec"),
        (re.compile(r"\bos\.(?:system|popen|spawn[a-z]*)\("), "Insecure process execution via os.system/popen"),
        (re.compile(r"\bpty\.spawn\("), "Interactive PTY spawn attempt"),
        (re.compile(r"\bpickle\.(?:loads?|Unpickler)\("), "Insecure deserialization via pickle"),
        (re.compile(r"\bsocket\.socket\("), "Direct network socket instantiation"),
        (re.compile(r"\bshutil\.rmtree\(['\"]/(?:[a-z0-9_-]+)?['\"]\)", re.IGNORECASE), "Dangerous root-level directory deletion"),
        (re.compile(r"(?i)(?:api_key|secret_key|private_key|token)\s*=\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]"), "Hardcoded credential or token detected"),
    ]

    @classmethod
    def audit_diff(cls, diff_text: str) -> tuple[bool, list[str]]:
        """Audits unified diff text for newly introduced security vulnerabilities.
        
        Returns:
            (is_safe, list_of_violations)
        """
        import textwrap
        violations: list[str] = []
        if not diff_text or not diff_text.strip():
            return True, []

        added_lines: list[str] = []
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added_lines.append(line[1:])

        added_content = "\n".join(added_lines)

        # 1. Regex pattern scans
        for pat, desc in cls.RISKY_PATTERNS:
            if pat.search(added_content):
                violations.append(desc)

        # 2. AST parsing of dedented added python code chunks
        try:
            tree = ast.parse(textwrap.dedent(added_content))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check direct name calls e.g. eval(), exec()
                    if isinstance(node.func, ast.Name) and node.func.id in cls.DANGEROUS_CALLS:
                        violations.append(f"Direct call to forbidden execution primitive: '{node.func.id}()'")
                    # Check dangerous subprocess calls with shell=True
                    elif isinstance(node.func, ast.Attribute) and node.func.attr in ("Popen", "run", "call", "check_call", "check_output"):
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                violations.append("Insecure subprocess invocation with shell=True")
        except Exception:
            pass

        return (len(violations) == 0, violations)


# ---------------------------------------------------------------------------
# 4. In-Memory SQLite Code Graph
# ---------------------------------------------------------------------------
class SQLiteCodeGraph:
    """Sub-5ms in-memory AST symbol and caller graph indexer."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.conn = sqlite3.connect(":memory:")
        self._init_schema()
        self.indexed = False

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE symbols (name TEXT, kind TEXT, file_path TEXT, lineno INTEGER);
            CREATE INDEX idx_sym ON symbols(name);
            CREATE TABLE calls (caller TEXT, callee TEXT, file_path TEXT, lineno INTEGER);
            CREATE INDEX idx_callee ON calls(callee);
            CREATE INDEX idx_caller ON calls(caller);
        """)
        self.conn.commit()

    def build_index(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM symbols")
        cur.execute("DELETE FROM calls")
        for py_file in self.workspace.glob("**/*.py"):
            rel = str(py_file.relative_to(self.workspace)).replace("\\", "/")
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        cur.execute("INSERT INTO symbols VALUES (?, 'function', ?, ?)", (node.name, rel, node.lineno))
                    elif isinstance(node, ast.ClassDef):
                        cur.execute("INSERT INTO symbols VALUES (?, 'class', ?, ?)", (node.name, rel, node.lineno))
                    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        cur.execute("INSERT INTO calls VALUES ('<caller>', ?, ?, ?)", (node.func.id, rel, getattr(node, 'lineno', 1)))
            except Exception:
                continue
        self.conn.commit()
        self.indexed = True

    def query_neighbors(
        self,
        symbol: str = "",
        node: str = "",
        direction: str = "incoming",
        edge_type: Optional[str] = None,
        max_neighbors: int = 50,
        limit: int = 50,
        **kwargs
    ) -> str:
        if not self.indexed:
            self.build_index()
        sym = symbol or node
        if not sym:
            return "[ERROR: No symbol specified]"
        cur = self.conn.cursor()
        matches = []
        effective_limit = min(max_neighbors, limit)
        if direction in ("incoming", "both"):
            cur.execute("SELECT file_path, lineno, caller FROM calls WHERE callee = ? LIMIT ?", (sym, effective_limit))
            for f, line, caller in cur.fetchall():
                matches.append(f"{f}:{line} -> calls {sym}()")
        if direction in ("outgoing", "both"):
            cur.execute("SELECT file_path, lineno, callee FROM calls WHERE caller = ? LIMIT ?", (sym, effective_limit))
            for f, line, callee in cur.fetchall():
                matches.append(f"{f}:{line} -> {sym}() calls {callee}")
        if not matches:
            cur.execute("SELECT file_path, lineno, kind FROM symbols WHERE name = ? LIMIT ?", (sym, effective_limit))
            for f, line, kind in cur.fetchall():
                matches.append(f"{f}:{line} -> defines {kind} {sym}")
        return "\n".join(matches[:effective_limit]) if matches else f"[No AST neighbors resolved for '{sym}']"

    def query_subgraph(self, symbol: str = "", nodes: Any = None, max_depth: int = 1, limit: int = 12, **kwargs) -> str:
        if nodes:
            symbol_list = [nodes] if isinstance(nodes, str) else list(nodes)
            parts = []
            for s in symbol_list[:6]:
                res = self.query_neighbors(symbol=str(s), direction="both", limit=limit)
                parts.append(f"--- Subgraph for '{s}' ---\n{res}")
            return "\n\n".join(parts)
        return self.query_neighbors(symbol=symbol, direction="both", limit=limit)


# ---------------------------------------------------------------------------
# 5. Production Tool Sandbox with Security Enforcements
# ---------------------------------------------------------------------------
class ToolSandbox:
    """Production air-gapped Tool Sandbox with built-in PathJail, CommandSanitizer,

    and SAST Patch Security Auditor.
    """

    def __init__(self, workspace_dir: str | Path = "/workspace", max_tool_budget: int = 30):
        self.workspace = Path(workspace_dir).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.jail = PathJail(self.workspace)
        self.budget = max_tool_budget
        self.calls_made = 0
        self.call_history: list[str] = []
        self.patch_submitted = False
        self.submitted_diff = ""
        self.graph = SQLiteCodeGraph(self.workspace)

    def reset_workspace(self, base_commit: Optional[str] = None) -> str:
        """Teardown repository modifications between tasks to prevent inter-task state leakage."""
        is_repo = (self.workspace / '.git').exists() or str(self.workspace) == '/workspace'
        if not is_repo:
            try:
                toplevel = subprocess.run(
                    ['git', '-C', str(self.workspace), 'rev-parse', '--show-toplevel'],
                    capture_output=True, text=True, timeout=5
                ).stdout.strip().replace('\\', '/').lower()
                is_repo = toplevel == str(self.workspace).replace('\\', '/').lower()
            except Exception:
                is_repo = False
        log = []
        if is_repo:
            cmds = [
                ['git', '-C', str(self.workspace), 'reset', '--hard', 'HEAD'],
                ['git', '-C', str(self.workspace), 'clean', '-fd']
            ]
            if base_commit:
                cmds.append(['git', '-C', str(self.workspace), 'checkout', '-f', base_commit])
            for cmd in cmds:
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if res.stdout.strip():
                        log.append(res.stdout.strip())
                except Exception as e:
                    log.append(f'Teardown note: {e}')
        else:
            log.append('[Standalone workspace reset]')
        self.calls_made = 0
        self.call_history = []
        self.patch_submitted = False
        self.submitted_diff = ''
        self.graph = SQLiteCodeGraph(self.workspace)
        return ' && '.join(log) if log else '[Workspace clean]'

    def _consume_budget(self, tool_name: str) -> None:
        self.calls_made += 1
        self.call_history.append(tool_name)
        if self.calls_made > self.budget:
            raise RuntimeError(f"Tool call budget exceeded ({self.budget} max calls).")

    def run_command(self, command: str, timeout: int = 120) -> str:
        self._consume_budget("run_command")
        try:
            # 1. Security Check
            CommandSanitizer.sanitize(command)
            # 2. Host Execution
            res = subprocess.run(
                command, shell=True, cwd=str(self.workspace),
                capture_output=True, text=True, timeout=timeout
            )
            output = (res.stdout or "") + (res.stderr or "")
            return output.strip() if output else "[Command executed with returncode 0 and no output]"
        except CommandSecurityViolation as csv:
            return f"[SECURITY_BLOCKED: {str(csv)}]"
        except subprocess.TimeoutExpired:
            return "[ERROR: Command timed out]"
        except Exception as e:
            return f"[ERROR: {str(e)}]"

    def read_file(self, path: str = "", filepath: str = "", start_line: int = 1, end_line: int = -1, **kwargs) -> str:
        self._consume_budget("read_file")
        target_path = filepath or path
        try:
            fp = self.jail.validate_read_path(target_path)
            if not fp.exists():
                return f"[ERROR: File '{target_path}' does not exist.]"
            lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
            total = len(lines)
            start = max(1, start_line) - 1
            end = total if end_line == -1 else min(total, end_line)
            snippet = lines[start:end]
            numbered = [f"{i + start + 1}: {line}" for i, line in enumerate(snippet)]
            return "\n".join(numbered)
        except SecurityJailViolation as sjv:
            return f"[SECURITY_ERROR: {str(sjv)}]"
        except Exception as e:
            return f"[ERROR: {str(e)}]"

    def edit_file(
        self,
        path: str = "",
        filepath: str = "",
        target: str = "",
        old_string: str = "",
        replacement: str = "",
        new_string: str = "",
        allow_multiple: bool = False,
        **kwargs
    ) -> str:
        self._consume_budget("edit_file")
        target_path = filepath or path
        old_block = old_string or target
        new_block = new_string or replacement
        try:
            fp = self.jail.validate_write_path(target_path, allow_scratch=False)
            if not fp.exists():
                return f"[ERROR: File '{target_path}' not found.]"
            content = fp.read_text(encoding="utf-8", errors="replace")
            if old_block not in content:
                return f"[ERROR: Target block not found in '{target_path}'. Ensure exact match.]"
            if content.count(old_block) > 1 and not allow_multiple:
                return f"[ERROR: Multiple occurrences found in '{target_path}'. Include more surrounding lines.]"
            new_content = content.replace(old_block, new_block, 1 if not allow_multiple else -1)
            fp.write_text(new_content, encoding="utf-8")
            return f"[SUCCESS: Replaced target block in {target_path}]"
        except SecurityJailViolation as sjv:
            return f"[SECURITY_ERROR: {str(sjv)}]"
        except Exception as e:
            return f"[ERROR: {str(e)}]"

    def write_file(self, path: str = "", filepath: str = "", content: str = "", **kwargs) -> str:
        self._consume_budget("write_file")
        target_path = filepath or path
        try:
            fp = self.jail.validate_write_path(target_path, allow_scratch=True)
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
            return f"[SUCCESS: Written {len(content)} bytes to {target_path}]"
        except SecurityJailViolation as sjv:
            return f"[SECURITY_ERROR: {str(sjv)}]"
        except Exception as e:
            return f"[ERROR: {str(e)}]"

    def get_status(self, **kwargs) -> str:
        self._consume_budget("get_status")
        try:
            diff_out = subprocess.run(["git", "-C", str(self.workspace), "status", "--short"], capture_output=True, text=True)
            stat = diff_out.stdout.strip() if diff_out.stdout else "[Clean working directory - no edits pending]"
        except Exception:
            stat = "[Git status check unavailable]"
        return f"Remaining Tool Budget: {self.budget - self.calls_made}/{self.budget}\nModified Files:\n{stat}"

    def submit_patch(self, **kwargs) -> str:
        self._consume_budget("submit_patch")
        try:
            diff_out = subprocess.run(["git", "-C", str(self.workspace), "diff"], capture_output=True, text=True)
            self.submitted_diff = diff_out.stdout
        except Exception:
            self.submitted_diff = ""

        # SAST Static Security Audit on generated diff
        is_safe, violations = PatchSecurityAuditor.audit_diff(self.submitted_diff)
        if not is_safe:
            return f"[SECURITY_REJECTED: Patch introduces high-risk patterns: {violations}]"

        self.patch_submitted = True
        return "[PATCH SUBMITTED SUCCESSFULLY]"

    def search_similar_code(self, query: str = "", top_k: int = 5, k: int = 5, **kwargs) -> str:
        self._consume_budget("search_similar_code")
        effective_k = k if k != 5 else top_k
        try:
            res = subprocess.run(["rg", "-i", "-n", query, str(self.workspace)], capture_output=True, text=True, timeout=30)
            lines = res.stdout.splitlines()[:effective_k]
            if lines:
                return "\n".join(lines)
        except Exception:
            pass
        matches = []
        for py_file in self.workspace.glob("**/*.py"):
            try:
                for i, line in enumerate(py_file.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                    if query.lower() in line.lower():
                        matches.append(f"{py_file.name}:{i}: {line.strip()}")
                        if len(matches) >= effective_k:
                            return "\n".join(matches)
            except Exception:
                continue
        return "\n".join(matches) if matches else f"[No matches found for '{query}']"

    def get_code_neighbors(
        self,
        symbol: str = "",
        node: str = "",
        direction: str = "incoming",
        edge_type: Optional[str] = None,
        max_neighbors: int = 50,
        **kwargs
    ) -> str:
        self._consume_budget("get_code_neighbors")
        return self.graph.query_neighbors(
            symbol=symbol, node=node, direction=direction, edge_type=edge_type, max_neighbors=max_neighbors
        )

    def get_code_subgraph(self, symbol: str = "", nodes: Any = None, max_depth: int = 1, **kwargs) -> str:
        self._consume_budget("get_code_subgraph")
        return self.graph.query_subgraph(symbol=symbol, nodes=nodes, max_depth=max_depth)
