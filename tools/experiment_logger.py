"""
tools/experiment_logger.py
==========================
Lightweight JSONL-based experiment logger for the Gemma 4 SWE Agent.

Records per-task metrics to a .jsonl file so performance can be measured
and compared across prompts, reasoning modes, and graph policies:
  - Mode A: Semantic-only
  - Mode B: Semantic + fixed graph
  - Mode C: Semantic + adaptive graph

Usage (from a harness or test script):
    from tools.experiment_logger import ExperimentLogger

    logger = ExperimentLogger("results/phase3_comparison.jsonl", mode="adaptive_graph")
    with logger.task("django__django-12345") as t:
        t.record_tool_call("search_similar_code")
        t.record_semantic_search()
        t.record_file_inspected("src/foo.py")
        t.record_symbol_inspected("QuerySet.filter")
        t.record_graph_call("get_code_neighbors")
        t.record_file_edited("src/foo.py")
        t.record_patch_size(14)
        t.record_test_attempt(passed=True)
        t.set_outcome("success")
    logger.close()
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator


# ── Task context ─────────────────────────────────────────────────────────────

class TaskRecord:
    """Mutable record for a single task execution in Phase 3."""

    def __init__(self, task_id: str, mode: str = "adaptive_graph", phase: str = "phase3"):
        self.task_id           = task_id
        self.mode              = mode          # semantic_only | fixed_graph | adaptive_graph
        self.phase             = phase
        self.outcome           = "error"       # updated by set_outcome()
        self.failure_reason: str | None = None
        self.notes: str | None          = None

        self._tool_calls: list[str] = []
        self._semantic_searches = 0
        self._graph_calls = 0
        self._symbols_inspected: list[str] = []
        self._files_inspected: list[str] = []
        self._files_edited: list[str] = []
        self._patch_size = 0
        self._test_attempts = 0
        self._tests_passed = 0
        self._repair_attempts = 0
        self._start = time.monotonic()
        self._start_ts = datetime.now(timezone.utc).isoformat()

    # ── Recording helpers ────────────────────────────────────────────────────

    def record_tool_call(self, tool_name: str) -> None:
        """Record any tool invocation."""
        self._tool_calls.append(tool_name)
        if tool_name == "search_similar_code":
            self._semantic_searches += 1
        elif tool_name in ("get_code_neighbors", "get_code_subgraph"):
            self._graph_calls += 1

    def record_semantic_search(self) -> None:
        """Increment count of semantic similarity searches."""
        self._semantic_searches += 1

    def record_graph_call(self, graph_tool: str = "get_code_neighbors") -> None:
        """Increment count of graph tool calls."""
        self._graph_calls += 1

    def record_symbol_inspected(self, symbol: str) -> None:
        """Record a symbol investigated via code-graph or AST reading."""
        if symbol and symbol not in self._symbols_inspected:
            self._symbols_inspected.append(symbol)

    def record_file_inspected(self, path: str) -> None:
        """Call when read_file or grep accesses a file."""
        if path and path not in self._files_inspected:
            self._files_inspected.append(path)

    def record_file_edited(self, path: str) -> None:
        """Call when edit_file or write_file modifies a workspace file."""
        if path and path not in self._files_edited:
            self._files_edited.append(path)

    def record_patch_size(self, lines: int) -> None:
        """Record line count of the final git patch."""
        self._patch_size = max(0, lines)

    def record_test_attempt(self, passed: bool) -> None:
        """Call once per test run."""
        self._test_attempts += 1
        if passed:
            self._tests_passed += 1

    def record_repair_attempt(self) -> None:
        """Call when a second (or later) edit is made after a test failure."""
        self._repair_attempts += 1

    def set_outcome(
        self,
        outcome: str,
        failure_reason: str | None = None,
        notes: str | None = None,
    ) -> None:
        """
        outcome: 'success' | 'failure' | 'partial' | 'error'
        failure_reason: short label, e.g. 'test_fail', 'no_edit', 'budget_exhausted'
        """
        self.outcome = outcome
        self.failure_reason = failure_reason
        self.notes = notes

    # ── Serialise ────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        elapsed = time.monotonic() - self._start
        return {
            "task_id":           self.task_id,
            "mode":              self.mode,
            "phase":             self.phase,
            "outcome":           self.outcome,
            "failure_reason":    self.failure_reason,
            "notes":             self.notes,
            "semantic_searches":     self._semantic_searches,
            "semantic_search_count": self._semantic_searches,
            "graph_calls":           self._graph_calls,
            "symbols_inspected":     self._symbols_inspected,
            "files_inspected":       self._files_inspected,
            "files_edited":          self._files_edited,
            "patch_size":            self._patch_size,
            "tool_calls":            len(self._tool_calls),
            "tool_call_trace":       self._tool_calls,
            "test_attempts":         self._test_attempts,
            "tests_passed":          self._tests_passed,
            "repair_attempts":       self._repair_attempts,
            "start_ts":              self._start_ts,
            "end_ts":                datetime.now(timezone.utc).isoformat(),
            "elapsed_s":             round(elapsed, 3),
            "elapsed_time":          round(elapsed, 3),
        }


# ── Logger ────────────────────────────────────────────────────────────────────

class ExperimentLogger:
    """
    Appends one JSON line per task to an output file.
    """

    def __init__(self, output_path: str | Path, mode: str = "adaptive_graph", phase: str = "phase3"):
        self._path  = Path(output_path)
        self._mode  = mode
        self._phase = phase
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("a", encoding="utf-8")
        self._open = True

    @contextmanager
    def task(self, task_id: str) -> Generator[TaskRecord, None, None]:
        """
        Context manager: yields a TaskRecord, then writes it on exit.
        """
        record = TaskRecord(task_id, mode=self._mode, phase=self._phase)
        try:
            yield record
        except Exception as exc:  # noqa: BLE001
            record.set_outcome("error", failure_reason=f"exception: {exc}")
            raise
        finally:
            self._write(record)

    def _write(self, record: TaskRecord) -> None:
        if self._open:
            self._fh.write(json.dumps(record.to_dict()) + "\n")
            self._fh.flush()

    def close(self) -> None:
        if self._open:
            self._fh.close()
            self._open = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
