"""
tools/run_baseline.py
=====================
Phase 4 Experiment runner for the Gemma 4 SWE Agent.

Supports evaluating and comparing four reasoning modes:
  A. mode_a: Semantic search + shell grep, no graph reasoning
  B. mode_b: Semantic + mandatory graph neighbor inspection on all candidates
  C. mode_c: Semantic + adaptive graph reasoning (Phase 3 frozen baseline)
  D. mode_d: Adaptive graph + structured patch planning + test-driven repair

Legacy mode names (semantic_only, fixed_graph, adaptive_graph) are accepted
for backward compatibility with Phase 3 result files.

Usage:
    python tools/run_baseline.py \\
        --tasks   data/tasks_sample.jsonl \\
        --results results/phase4_mode_d.jsonl \\
        --mode    mode_d \\
        --phase   phase4 \\
        [--limit  N]

This script is local tooling and NOT included in submission.zip.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.experiment_logger import ExperimentLogger  # noqa: E402


DEFAULT_TIMEOUT_S = 600
TOOL_PATTERN = re.compile(
    r"(run_command|read_file|edit_file|write_file|get_status"
    r"|submit_patch|search_similar_code|get_code_neighbors|get_code_subgraph)"
)
EDIT_PATTERN    = re.compile(r"(edit_file|write_file)\s*[:\(].*?([\/\w\.\-]+\.\w+)")
READ_PATTERN    = re.compile(r"read_file\s*[:\(].*?([\/\w\.\-]+\.\w+)")
GRAPH_PATTERN   = re.compile(r"(get_code_neighbors|get_code_subgraph)\s*[:\(]")
SYMBOL_PATTERN  = re.compile(r"(?:symbol|target)\s*=\s*['\"]?([\w\.\-]+)['\"]?")
REPAIR_SIGNAL   = re.compile(r"(repair|retry|re-test|attempt \d)")

# Canonical Phase 4 mode names + Phase 3 legacy aliases for backward compat
MODE_CHOICES = [
    "mode_a", "mode_b", "mode_c", "mode_d",
    "semantic_only", "fixed_graph", "adaptive_graph",
]

# Mode D -- structured internal state signal extraction
CONFIDENCE_PATTERN = re.compile(r"Confidence\s*:\s*(high|medium|low)", re.IGNORECASE)
PATCH_PLAN_PATTERN = re.compile(r"Patch Plan\s*:", re.IGNORECASE)
TDR_CLASS_PATTERN  = re.compile(r"(PATCH_DEFECT|PRE_EXISTING|BUDGET_LOW)")


def load_tasks(path: Path, limit: int | None = None) -> list[dict]:
    tasks = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    if limit:
        tasks = tasks[:limit]
    print(f"Loaded {len(tasks)} task(s) from {path}")
    return tasks


def run_tests(repo: str, test_cmd: str, pass_regex: str | None) -> tuple[bool, str]:
    """Run test command in target repo."""
    try:
        result = subprocess.run(
            test_cmd,
            shell=True,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        if pass_regex:
            passed = bool(re.search(pass_regex, output, re.IGNORECASE))
        else:
            passed = result.returncode == 0
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TEST TIMEOUT"
    except Exception as exc:  # noqa: BLE001
        return False, f"TEST ERROR: {exc}"


def compute_patch_size(repo: str) -> int:
    """Calculate lines changed in git diff."""
    if not repo or not Path(repo).exists():
        return 0
    try:
        res = subprocess.run(
            ["git", "-C", repo, "diff", "--numstat"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        total_lines = 0
        for line in res.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                total_lines += int(parts[0]) + int(parts[1])
        return total_lines
    except Exception:  # noqa: BLE001
        return 0


def parse_agent_output(output: str) -> dict:
    """Extract metric signals from agent execution traces."""
    tool_calls   = TOOL_PATTERN.findall(output)
    edited_files = [m[1] for m in EDIT_PATTERN.findall(output)]
    read_matches = READ_PATTERN.findall(output)
    symbols      = SYMBOL_PATTERN.findall(output)
    repair_count = len(REPAIR_SIGNAL.findall(output))

    semantic_count = sum(1 for t in tool_calls if t == "search_similar_code")
    graph_count    = sum(1 for t in tool_calls if t in ("get_code_neighbors", "get_code_subgraph"))

    # Mode D — structured state signals
    confidence_match = CONFIDENCE_PATTERN.search(output)
    confidence = confidence_match.group(1).lower() if confidence_match else None
    patch_plan_set  = bool(PATCH_PLAN_PATTERN.search(output))
    tdr_failure_classes = TDR_CLASS_PATTERN.findall(output)

    return {
        "tool_call_trace":    tool_calls,
        "semantic_searches":  semantic_count,
        "graph_calls":        graph_count,
        "symbols_inspected":  list(dict.fromkeys(symbols)),
        "files_inspected":    list(dict.fromkeys(read_matches)),
        "files_edited":       list(dict.fromkeys(edited_files)),
        "repair_attempts":    repair_count,
        # Mode D extras
        "confidence":         confidence,
        "patch_plan_set":     patch_plan_set,
        "tdr_failure_classes": tdr_failure_classes,
    }


def run_mock_agent(task: dict, mode: str, timeout: int) -> tuple[str, str]:
    """
    Placeholder harness call. When real competition swegemma harness
    is available, this invokes the model with the configured mode.
    """
    print(f"  [MOCK] Running agent (mode={mode}) on task: {task['task_id']}")
    return "", ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Gemma 4 SWE Agent Phase 4 baseline.")
    parser.add_argument("--tasks",   required=True, help="Path to tasks.jsonl")
    parser.add_argument("--results", required=True, help="Output results.jsonl path")
    parser.add_argument("--mode",    default="mode_d",
                        choices=MODE_CHOICES,
                        help="Reasoning policy mode (mode_a/b/c/d or legacy names)")
    parser.add_argument("--phase",   default="phase4", help="Phase label")
    parser.add_argument("--limit",   type=int, default=None, help="Task limit")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S, help="Timeout per task")
    args = parser.parse_args()

    tasks_path   = Path(args.tasks)
    results_path = Path(args.results)

    if not tasks_path.exists():
        print(f"ERROR: tasks file not found: {tasks_path}")
        sys.exit(1)

    tasks = load_tasks(tasks_path, limit=args.limit)

    with ExperimentLogger(results_path, mode=args.mode, phase=args.phase) as logger:
        for i, task in enumerate(tasks, 1):
            task_id  = task.get("task_id", f"task_{i}")
            repo     = task.get("repo", "")
            test_cmd = task.get("test_cmd", "")
            pass_rx  = task.get("pass_regex")

            print(f"\n[{i}/{len(tasks)}] {task_id} [Mode: {args.mode}]")

            with logger.task(task_id) as t:
                start = time.monotonic()

                # Pre-patch validation
                pre_passed = False
                if test_cmd and repo:
                    pre_passed, _ = run_tests(repo, test_cmd, pass_rx)
                    t.record_test_attempt(passed=pre_passed)
                    print(f"  pre-patch tests: {'PASS' if pre_passed else 'FAIL'}")

                # Agent execution
                agent_stdout, agent_stderr = run_mock_agent(task, mode=args.mode, timeout=args.timeout)

                # Instrument metrics
                metrics = parse_agent_output(agent_stdout + agent_stderr)
                for tool in metrics["tool_call_trace"]:
                    t.record_tool_call(tool)
                for s in metrics["symbols_inspected"]:
                    t.record_symbol_inspected(s)
                for f in metrics["files_inspected"]:
                    t.record_file_inspected(f)
                for f in metrics["files_edited"]:
                    t.record_file_edited(f)
                for _ in range(metrics["repair_attempts"]):
                    t.record_repair_attempt()

                # Mode D structured state signals
                if metrics.get("confidence"):
                    t.record_confidence(metrics["confidence"])
                if metrics.get("patch_plan_set"):
                    t.record_patch_plan_set()
                for cls in metrics.get("tdr_failure_classes", []):
                    t.record_tdr_failure_class(cls)

                patch_lines = compute_patch_size(repo)
                t.record_patch_size(patch_lines)

                # Post-patch validation
                post_passed = False
                if test_cmd and repo:
                    post_passed, _ = run_tests(repo, test_cmd, pass_rx)
                    t.record_test_attempt(passed=post_passed)
                    print(f"  post-patch tests: {'PASS' if post_passed else 'FAIL'}")

                # Classify outcome
                if post_passed and not pre_passed:
                    t.set_outcome("success")
                elif post_passed and pre_passed:
                    t.set_outcome("partial", notes="tests passed pre-patch too")
                elif not metrics["files_edited"]:
                    t.set_outcome("failure", failure_reason="no_edit")
                else:
                    t.set_outcome("failure", failure_reason="test_fail")

                elapsed = time.monotonic() - start
                print(f"  elapsed: {elapsed:.1f}s  outcome: {t.outcome}")

    print(f"\nResults written to: {results_path}")


if __name__ == "__main__":
    main()
