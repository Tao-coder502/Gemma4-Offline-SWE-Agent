from __future__ import annotations

import ast
import sqlite3
from pathlib import Path
from typing import List


class InMemoryCodeGraph:
    """Sub‑5ms symbol indexer using an in‑memory SQLite database.

    The graph stores two tables:
    * ``symbols`` – ``name``, ``kind`` (function/class), ``file_path`` and ``lineno``
    * ``calls``   – ``caller`` (placeholder), ``callee``, ``file_path`` and ``lineno``
    """

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.conn = sqlite3.connect(":memory:")
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE symbols (name TEXT, kind TEXT, file_path TEXT, lineno INTEGER);
            CREATE INDEX idx_sym ON symbols(name);
            CREATE TABLE calls (caller TEXT, callee TEXT, file_path TEXT, lineno INTEGER);
            CREATE INDEX idx_callee ON calls(callee);
            """
        )
        self.conn.commit()

    def build_index(self) -> None:
        """Walk the workspace, parse every ``*.py`` file and populate the tables.

        Errors while parsing a file are ignored – they rarely affect the
        symbol‑search use‑cases and keep the indexing robust on messy repos.
        """
        cur = self.conn.cursor()
        for py_file in self.workspace.rglob("*.py"):
            # Store paths with forward slashes for consistency across OSes
            rel = str(py_file.relative_to(self.workspace)).replace("\\", "/")
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        cur.execute(
                            "INSERT INTO symbols VALUES (?, 'function', ?, ?)",
                            (node.name, rel, node.lineno),
                        )
                    elif isinstance(node, ast.ClassDef):
                        cur.execute(
                            "INSERT INTO symbols VALUES (?, 'class', ?, ?)",
                            (node.name, rel, node.lineno),
                        )
                    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        cur.execute(
                            "INSERT INTO calls VALUES ('<caller>', ?, ?, ?)",
                            (node.func.id, rel, getattr(node, "lineno", 1)),
                        )
            except Exception:
                # Silently skip files that cannot be parsed (e.g., syntax errors)
                continue
        self.conn.commit()

    def query(self, symbol: str) -> List[str]:
        """Return a list of human‑readable matches for *symbol*.

        The result includes both definitions and call sites.
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT file_path, lineno, kind FROM symbols WHERE name = ?", (symbol,)
        )
        res = [f"{f}:{line} (defines {kind} {symbol})" for f, line, kind in cur.fetchall()]
        cur.execute("SELECT file_path, lineno FROM calls WHERE callee = ?", (symbol,))
        res += [f"{f}:{line} (calls {symbol})" for f, line in cur.fetchall()]
        return res
