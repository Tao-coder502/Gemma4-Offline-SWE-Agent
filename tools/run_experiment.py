#!/usr/bin/env python3
"""
tools/run_experiment.py
=======================
Phase 4 top-level experiment orchestrator for the Gemma 4 SWE Agent.

Runs all four experimental modes (A, B, C, D) against the same task set,
writes per-mode JSONL result files, then automatically calls
analyze_results.py to produce a comparative report.

This script is the single entry point for reproducing the Phase 4
ablation study. All four modes are run in the SAME Python process
sequentially, using the mock harness. Replace run_mock_agent() in
run_baseline.py with the real competition harness before evaluation.

Usage:
    python tools/run_experiment.py \\
        --tasks  data/tasks_sample.jsonl \\
        --outdir results/phase4_ablation \\
        [--modes a b c d] \\
        [--limit N] \\
        [--phase phase4]

Output structure:
    results/phase4_ablation/
        mode_a.jsonl
        mode_b.jsonl
        mode_c.jsonl
        mode_d.jsonl
        comparison_report.txt

This script is local tooling and NOT included in submission.zip.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


# Mapping from short label to run_baseline.py --mode value
MODE_MAP = {
    "a": "mode_a",
    "b": "mode_b",
    "c": "mode_c",
    "d": "mode_d",
}


def run_mode(
    mode_key: str,
    tasks: Path,
    outdir: Path,
    phase: str,
    limit: int | None,
    timeout: int,
) -> Path:
    """Invoke run_baseline.py for a single mode and return the result path."""
    mode_name = MODE_MAP[mode_key]
    result_file = outdir / f"{mode_name}.jsonl"
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "run_baseline.py"),
        "--tasks",   str(tasks),
        "--results", str(result_file),
        "--mode",    mode_name,
        "--phase",   phase,
        "--timeout", str(timeout),
    ]
    if limit is not None:
        cmd += ["--limit", str(limit)]

    print(f"\n{'=' * 60}")
    print(f"  EXPERIMENT MODE {mode_key.upper()} ({mode_name})")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[WARN] Mode {mode_key.upper()} exited with code {result.returncode}")
    return result_file


def run_comparison(result_files: list[Path]) -> None:
    """Call analyze_results.py in --compare mode."""
    existing = [str(f) for f in result_files if f.exists()]
    if len(existing) < 2:
        print("[WARN] Fewer than 2 result files exist — skipping comparison.")
        return

    cmd = [
        sys.executable,
        str(Path(__file__).parent / "analyze_results.py"),
        "--compare",
        *existing,
    ]
    print(f"\n{'=' * 60}")
    print("  COMPARATIVE ANALYSIS REPORT")
    print(f"{'=' * 60}")
    subprocess.run(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 4 experiment orchestrator: run all modes and compare results."
    )
    parser.add_argument(
        "--tasks", required=True, help="Path to tasks JSONL file"
    )
    parser.add_argument(
        "--outdir", default="results/phase4_ablation",
        help="Directory to write per-mode result files"
    )
    parser.add_argument(
        "--modes", nargs="+", default=["a", "b", "c", "d"],
        choices=["a", "b", "c", "d"],
        help="Which experiment modes to run (default: all four)"
    )
    parser.add_argument(
        "--phase", default="phase4", help="Phase label written into each result record"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of tasks per mode"
    )
    parser.add_argument(
        "--timeout", type=int, default=600, help="Per-task timeout seconds"
    )
    parser.add_argument(
        "--no-compare", action="store_true",
        help="Skip the automatic comparative analysis at the end"
    )
    args = parser.parse_args()

    tasks_path = Path(args.tasks)
    if not tasks_path.exists():
        print(f"[ERROR] Tasks file not found: {tasks_path}")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    result_files: list[Path] = []
    for mode_key in args.modes:
        result_file = run_mode(
            mode_key=mode_key,
            tasks=tasks_path,
            outdir=outdir,
            phase=args.phase,
            limit=args.limit,
            timeout=args.timeout,
        )
        result_files.append(result_file)

    if not args.no_compare:
        run_comparison(result_files)

    print(f"\nAll results written to: {outdir}")


if __name__ == "__main__":
    main()
