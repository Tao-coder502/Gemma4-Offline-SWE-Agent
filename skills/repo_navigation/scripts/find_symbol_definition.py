#!/usr/bin/env python3
"""
Locates class and function definitions across Python files in a workspace using AST.
Usage: python find_symbol_definition.py <symbol_name> [workspace_dir]
"""

import sys
import ast
from pathlib import Path

def find_symbol(symbol: str, workspace: Path):
    matches = []
    for py_file in workspace.rglob("*.py"):
        # Skip hidden, virtualenv, and build directories
        parts = py_file.parts
        if any(p.startswith(".") or p in ("build", "dist", "venv", ".venv", "__pycache__") for p in parts):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name == symbol:
                        rel = py_file.relative_to(workspace)
                        matches.append((str(rel), node.lineno, type(node).__name__))
        except Exception:
            continue
    return matches

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_symbol_definition.py <symbol_name> [workspace_dir]")
        sys.exit(1)
    
    target_sym = sys.argv[1]
    ws = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/workspace")
    if not ws.exists():
        ws = Path(".")
    
    results = find_symbol(target_sym, ws)
    if not results:
        print(f"Symbol '{target_sym}' not found in {ws}")
    else:
        print(f"Found {len(results)} match(es) for '{target_sym}':")
        for filepath, lineno, kind in results:
            print(f"  - {filepath}:{lineno} ({kind})")
