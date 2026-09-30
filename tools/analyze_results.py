#!/usr/bin/env python3
"""
tools/analyze_results.py
========================
Research-grade experiment metric analyzer and comparative evaluator.

Audits and compares SWE agent experiment runs:
  - Single-mode summary reports
  - Multi-mode cross-comparison tables
  - Task-level outcome matrices
  - Paired-transition outcome calculations
  - Failure taxonomy breakdown

Supports arbitrary evaluation sets (N = 8, 20, 50, 100+).
Calculates all statistics strictly from raw task-level records.

Usage:
    python tools/analyze_results.py --results results/phase2_pilot/phase2_baseline_pilot.jsonl
    python tools/analyze_results.py --compare \\
        results/phase3_pilot/mode_a_semantic_pilot.jsonl \\
        results/phase3_pilot/mode_b_fixed_graph_pilot.jsonl \\
        results/phase3_pilot/mode_c_adaptive_graph_pilot.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def safe_div(num: float, den: float) -> float:
    """Safe division returning 0.0 when denominator is 0."""
    return (num / den) if den != 0 else 0.0


def load_records(path: Path) -> list[dict]:
    """Load and validate records from a JSONL file."""
    records = []
    if not path.exists():
        print(f"[ERROR] Results file not found: {path}")
        sys.exit(1)

    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"[WARN] Line {lineno} in {path.name} is invalid JSON: {exc}")
    return records


def normalize_record(r: dict) -> dict:
    """Normalize field names and aliases across phases."""
    task_id = r.get("task_id", "unknown")
    mode = r.get("mode", "unspecified")
    phase = r.get("phase", "unknown")
    outcome = r.get("outcome", "unknown")
    failure_reason = r.get("failure_reason")

    # Semantic search count alias
    semantic_count = r.get("semantic_searches")
    if semantic_count is None:
        semantic_count = r.get("semantic_search_count", 0)

    # Graph calls
    graph_count = r.get("graph_calls", 0)

    # Elapsed time alias
    elapsed = r.get("elapsed_s")
    if elapsed is None:
        elapsed = r.get("elapsed_time", 0.0)

    # Patch size alias
    patch_size = r.get("patch_size")
    if patch_size is None:
        patch_size = r.get("lines_changed", 0)

    # Files inspected alias
    files_inspected = r.get("files_inspected")
    if files_inspected is None:
        files_inspected = r.get("files_read", [])

    return {
        "task_id": task_id,
        "mode": mode,
        "phase": phase,
        "outcome": outcome,
        "failure_reason": failure_reason,
        "notes": r.get("notes"),
        "tool_calls": r.get("tool_calls", 0),
        "tool_call_trace": r.get("tool_call_trace", []),
        "semantic_searches": semantic_count,
        "graph_calls": graph_count,
        "symbols_inspected": r.get("symbols_inspected", []),
        "files_inspected": files_inspected,
        "files_edited": r.get("files_edited", []),
        "patch_size": patch_size,
        "test_attempts": r.get("test_attempts", 0),
        "tests_passed": r.get("tests_passed", 0),
        "repair_attempts": r.get("repair_attempts", 0),
        "elapsed_s": float(elapsed) if elapsed is not None else 0.0,
    }


def analyze(raw_records: list[dict]) -> dict:
    """Compute verified aggregate statistics from raw task records."""
    if not raw_records:
        return {}

    records = [normalize_record(r) for r in raw_records]
    total = len(records)

    outcomes = Counter(r["outcome"] for r in records)
    failure_reasons = Counter(r["failure_reason"] for r in records if r["failure_reason"])

    tool_counts: Counter[str] = Counter()
    total_tool_calls = 0
    total_semantic_searches = 0
    total_graph_calls = 0
    total_files_inspected = 0
    total_files_edited = 0
    total_symbols_inspected = 0
    total_patch_lines = 0
    total_test_attempts = 0
    total_tests_passed = 0
    total_repair_attempts = 0
    durations: list[float] = []

    for r in records:
        total_tool_calls += r["tool_calls"]
        for t in r["tool_call_trace"]:
            tool_counts[t] += 1

        total_semantic_searches += r["semantic_searches"]
        total_graph_calls += r["graph_calls"]
        total_symbols_inspected += len(r["symbols_inspected"])
        total_files_inspected += len(r["files_inspected"])
        total_files_edited += len(r["files_edited"])
        total_patch_lines += r["patch_size"]
        total_test_attempts += r["test_attempts"]
        total_tests_passed += r["tests_passed"]
        total_repair_attempts += r["repair_attempts"]
        durations.append(r["elapsed_s"])

    resolved = outcomes.get("success", 0)
    success_rate = safe_div(resolved, total) * 100.0

    return {
        "records": records,
        "mode": records[0]["mode"] if records else "unknown",
        "phase": records[0]["phase"] if records else "unknown",
        "total_tasks": total,
        "resolved_tasks": resolved,
        "outcomes": outcomes,
        "success_rate": success_rate,
        "failure_reasons": failure_reasons,
        "total_tool_calls": total_tool_calls,
        "avg_tool_calls": safe_div(total_tool_calls, total),
        "total_semantic_searches": total_semantic_searches,
        "avg_semantic_searches": safe_div(total_semantic_searches, total),
        "total_graph_calls": total_graph_calls,
        "avg_graph_calls": safe_div(total_graph_calls, total),
        "avg_symbols_inspected": safe_div(total_symbols_inspected, total),
        "avg_files_inspected": safe_div(total_files_inspected, total),
        "avg_files_edited": safe_div(total_files_edited, total),
        "avg_patch_size": safe_div(total_patch_lines, total),
        "tool_distribution": tool_counts,
        "total_test_attempts": total_test_attempts,
        "total_tests_passed": total_tests_passed,
        "total_repair_attempts": total_repair_attempts,
        "avg_repair_attempts": safe_div(total_repair_attempts, total),
        "avg_elapsed_s": safe_div(sum(durations), len(durations)),
        "min_elapsed_s": min(durations) if durations else 0.0,
        "max_elapsed_s": max(durations) if durations else 0.0,
        "total_elapsed_s": sum(durations),
    }


def print_single_report(stats: dict, file_path: Path) -> None:
    """Print an auditable single-run report."""
    if not stats:
        print("[WARN] No records to analyze.")
        return

    total = stats["total_tasks"]
    print("=" * 70)
    print(f" EXPERIMENT AUDIT REPORT: {file_path.name}")
    print(f" Phase: {stats['phase']} | Mode: {stats['mode']} | Sample Size (N): {total}")
    print("=" * 70)

    print("\n-- 1. PRIMARY EVALUATION METRIC " + "-" * 38)
    print(f"  Patch Success Rate:     {stats['success_rate']:.1f}% ({stats['resolved_tasks']} / {total} tasks resolved)")

    print("\n-- 2. OUTCOME DISTRIBUTION " + "-" * 43)
    for outcome, cnt in sorted(stats["outcomes"].items()):
        pct = safe_div(cnt, total) * 100.0
        print(f"    - {outcome:<14}: {cnt:>3} ({pct:>5.1f}%)")

    if stats["failure_reasons"]:
        print("\n-- 3. FAILURE TAXONOMY BREAKDOWN " + "-" * 37)
        for reason, cnt in stats["failure_reasons"].most_common():
            pct = safe_div(cnt, total) * 100.0
            print(f"    - {reason:<22}: {cnt:>3} ({pct:>5.1f}%)")

    print("\n-- 4. REPOSITORY LOCALIZATION & GRAPH CALLS " + "-" * 26)
    print(f"  Semantic Searches (total / avg): {stats['total_semantic_searches']} ({stats['avg_semantic_searches']:.2f} / task)")
    print(f"  Graph Calls (total / avg):       {stats['total_graph_calls']} ({stats['avg_graph_calls']:.2f} / task)")
    print(f"  Avg Symbols Inspected:           {stats['avg_symbols_inspected']:.2f} / task")
    print(f"  Avg Files Inspected:             {stats['avg_files_inspected']:.2f} / task")
    print(f"  Avg Files Edited:                {stats['avg_files_edited']:.2f} / task")
    print(f"  Avg Patch Size (lines):          {stats['avg_patch_size']:.1f} lines")

    print("\n-- 5. TOOL BUDGET & EXECUTION LATENCY " + "-" * 31)
    print(f"  Total Tool Invocations:          {stats['total_tool_calls']}")
    print(f"  Avg Tool Invocations / Task:     {stats['avg_tool_calls']:.2f}")
    print(f"  Total Test Attempts:             {stats['total_test_attempts']}")
    print(f"  Avg Repair Cycles / Task:        {stats['avg_repair_attempts']:.2f}")
    print(f"  Avg Wall-Clock Time / Task:      {stats['avg_elapsed_s']:.1f}s")
    print(f"  Total Benchmark Runtime:         {stats['total_elapsed_s']:.1f}s ({stats['total_elapsed_s'] / 60.0:.1f} min)")
    print("=" * 70)


def print_comparison_tables(results_list: list[tuple[str, dict]]) -> None:
    """Print cross-mode comparative table, task matrix, and paired transitions."""
    print("=" * 88)
    print(" EXPERIMENT COMPARISON & PAIRED TRANSITION AUDIT")
    print("=" * 88)

    # 1. Summary comparison table
    header = f"{'Metric':<28} | " + " | ".join(f"{name:<16}" for name, _ in results_list)
    print(header)
    print("-" * len(header))

    metrics = [
        ("Patch Success Rate", lambda s: f"{s['success_rate']:.1f}%"),
        ("Resolved Tasks", lambda s: f"{s['resolved_tasks']} / {s['total_tasks']}"),
        ("Avg Tool Calls / Task", lambda s: f"{s['avg_tool_calls']:.2f}"),
        ("Avg Semantic Searches", lambda s: f"{s['avg_semantic_searches']:.2f}"),
        ("Avg Graph Calls / Task", lambda s: f"{s['avg_graph_calls']:.2f}"),
        ("Total Graph Calls", lambda s: f"{s['total_graph_calls']}"),
        ("Avg Symbols Inspected", lambda s: f"{s['avg_symbols_inspected']:.2f}"),
        ("Avg Files Inspected", lambda s: f"{s['avg_files_inspected']:.2f}"),
        ("Avg Files Edited", lambda s: f"{s['avg_files_edited']:.2f}"),
        ("Avg Patch Size (lines)", lambda s: f"{s['avg_patch_size']:.1f}"),
        ("Avg Repairs / Task", lambda s: f"{s['avg_repair_attempts']:.2f}"),
        ("Avg Elapsed Time (s)", lambda s: f"{s['avg_elapsed_s']:.1f}s"),
    ]

    for label, extractor in metrics:
        row = f"{label:<28} | " + " | ".join(f"{extractor(s):<16}" for _, s in results_list)
        print(row)
    print("-" * len(header))

    # 2. Task-level outcome matrix
    # Map tasks across runs
    mode_task_map: dict[str, dict[str, dict]] = {}
    all_task_ids: list[str] = []
    for name, stats in results_list:
        mode_task_map[name] = {r["task_id"]: r for r in stats.get("records", [])}
        for r in stats.get("records", []):
            if r["task_id"] not in all_task_ids:
                all_task_ids.append(r["task_id"])

    print("\n-- TASK-LEVEL OUTCOME MATRIX " + "-" * 59)
    matrix_hdr = f"{'Task ID':<30} | " + " | ".join(f"{name:<16}" for name, _ in results_list)
    print(matrix_hdr)
    print("-" * len(matrix_hdr))

    for tid in all_task_ids:
        outcomes = []
        for name, _ in results_list:
            rec = mode_task_map[name].get(tid)
            if rec:
                out = "PASS" if rec["outcome"] == "success" else f"FAIL ({rec.get('failure_reason') or 'fail'})"
            else:
                out = "N/A"
            outcomes.append(f"{out:<16}")
        print(f"{tid:<30} | " + " | ".join(outcomes))
    print("-" * len(matrix_hdr))

    # 3. Paired transition calculations (if 3 modes A, B, C provided)
    if len(results_list) >= 3:
        name_a, stats_a = results_list[0]
        name_b, stats_b = results_list[1]
        name_c, stats_c = results_list[2]

        map_a = mode_task_map[name_a]
        map_b = mode_task_map[name_b]
        map_c = mode_task_map[name_c]

        a_fail_b_pass = []
        a_fail_c_pass = []
        b_fail_c_pass = []
        a_pass_c_fail = []
        b_pass_c_fail = []
        all_fail = []

        for tid in all_task_ids:
            res_a = map_a.get(tid, {}).get("outcome") == "success"
            res_b = map_b.get(tid, {}).get("outcome") == "success"
            res_c = map_c.get(tid, {}).get("outcome") == "success"

            if not res_a and res_b:
                a_fail_b_pass.append(tid)
            if not res_a and res_c:
                a_fail_c_pass.append(tid)
            if not res_b and res_c:
                b_fail_c_pass.append(tid)
            if res_a and not res_c:
                a_pass_c_fail.append(tid)
            if res_b and not res_c:
                b_pass_c_fail.append(tid)
            if not res_a and not res_b and not res_c:
                all_fail.append(tid)

        print("\n-- PAIRED TRANSITIONS & DESCRIPTIVE OUTCOMES " + "-" * 42)
        print(f"  {name_a} FAIL  ->  {name_b} PASS : {len(a_fail_b_pass):>2} tasks {a_fail_b_pass}")
        print(f"  {name_a} FAIL  ->  {name_c} PASS : {len(a_fail_c_pass):>2} tasks {a_fail_c_pass}")
        print(f"  {name_b} FAIL  ->  {name_c} PASS : {len(b_fail_c_pass):>2} tasks {b_fail_c_pass}")
        print(f"  {name_a} PASS  ->  {name_c} FAIL : {len(a_pass_c_fail):>2} tasks {a_pass_c_fail}")
        print(f"  {name_b} PASS  ->  {name_c} FAIL : {len(b_pass_c_fail):>2} tasks {b_pass_c_fail}")
        print(f"  ALL MODES FAILED             : {len(all_fail):>2} tasks {all_fail}")
        print("  (Note: Paired transitions describe observed task shifts; they do not constitute causal proof.)")

    print("=" * 88)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze and compare SWE agent experiment results.")
    parser.add_argument("--results", help="Path to single results JSONL file")
    parser.add_argument("--compare", nargs="+", help="Paths to 2 or more results JSONL files to compare")
    args = parser.parse_args()

    if args.compare:
        results_list = []
        for path_str in args.compare:
            p = Path(path_str)
            records = load_records(p)
            stats = analyze(records)
            mode_label = stats.get("mode")
            if not mode_label or mode_label == "unspecified":
                mode_label = p.stem
            results_list.append((mode_label, stats))
        print_comparison_tables(results_list)
        return

    if not args.results:
        print("Error: Specify --results <path> or --compare <file1> <file2> ...")
        sys.exit(1)

    results_path = Path(args.results)
    records = load_records(results_path)
    stats = analyze(records)
    print_single_report(stats, results_path)


if __name__ == "__main__":
    main()
