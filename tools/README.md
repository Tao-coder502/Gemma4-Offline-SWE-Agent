# Experiment & Baseline Tools (Phase 3)

This directory contains local offline experiment, logging, and evaluation utilities for the **Gemma 4 Offline SWE Agent**.

> **Note**: These files are developer tooling and are **NOT** packaged into `submission.zip`. They run strictly outside the competition evaluation harness.

---

## Files Overview

| Script | Purpose |
|---|---|
| `experiment_logger.py` | JSONL logging engine. Provides `ExperimentLogger` and `TaskRecord` to record per-task metrics across Phase 3 reasoning modes (`semantic_only`, `fixed_graph`, `adaptive_graph`). |
| `run_baseline.py` | Local task runner that executes benchmarks, runs pre/post test commands, traces tool calls and graph queries, and outputs JSONL results. |
| `analyze_results.py` | Result aggregator that generates statistical summaries, single-mode reports, and cross-mode comparative evaluation tables (`--compare`). |

---

## Phase 3 Experiment Metrics Tracked

In accordance with Phase 3 research objectives, runs track:

1. **Issue outcome**: `success`, `failure`, `partial`, `error`
2. **Failure reason**: explicit classification (`test_fail`, `no_edit`, `budget_exhausted`, `syntax_error`, etc.)
3. **Reasoning mode**: `semantic_only`, `fixed_graph`, or `adaptive_graph`
4. **Semantic searches**: count of `search_similar_code` invocations
5. **Graph calls**: count of `get_code_neighbors` + `get_code_subgraph` invocations
6. **Symbols inspected**: distinct list of function and class symbols investigated
7. **Files inspected**: distinct list of source files read with `read_file`
8. **Files edited**: distinct list of source files modified with `edit_file` / `write_file`
9. **Patch size**: total added and deleted line count of the final diff
10. **Test attempts & passes**: pre-patch and post-patch test invocations
11. **Repair attempts**: number of modification cycles following test failure
12. **Execution time**: elapsed wall-clock seconds per task

---

## JSONL Output Schema (Phase 3)

```json
{
  "task_id": "pytest-dev__pytest-5221",
  "mode": "adaptive_graph",
  "phase": "phase3",
  "outcome": "success",
  "failure_reason": null,
  "notes": "Dispatched fixture scope localized via get_code_neighbors on getfixturedefs",
  "semantic_searches": 1,
  "graph_calls": 1,
  "symbols_inspected": ["FixtureManager.getfixturedefs"],
  "files_inspected": ["src/_pytest/fixtures.py"],
  "files_edited": ["src/_pytest/fixtures.py"],
  "patch_size": 11,
  "tool_calls": 10,
  "tool_call_trace": [
    "run_command",
    "search_similar_code",
    "read_file",
    "get_code_neighbors",
    "read_file",
    "edit_file",
    "run_command",
    "get_status",
    "submit_patch"
  ],
  "test_attempts": 2,
  "tests_passed": 1,
  "repair_attempts": 0,
  "start_ts": "2026-10-01T00:00:00.000000+00:00",
  "end_ts": "2026-10-01T00:01:32.000000+00:00",
  "elapsed_s": 92.5
}
```

---

## Usage Guide

### 1. Running an Evaluation in a Specific Mode

```bash
# Mode C: Adaptive Graph Reasoning (Recommended Default)
python tools/run_baseline.py \
    --tasks data/tasks_sample.jsonl \
    --results results/phase3_mode_c_adaptive_graph.jsonl \
    --mode adaptive_graph \
    --phase phase3

# Mode A: Semantic-Only Baseline
python tools/run_baseline.py \
    --tasks data/tasks_sample.jsonl \
    --results results/phase3_mode_a_semantic.jsonl \
    --mode semantic_only

# Mode B: Fixed Graph Baseline
python tools/run_baseline.py \
    --tasks data/tasks_sample.jsonl \
    --results results/phase3_mode_b_fixed_graph.jsonl \
    --mode fixed_graph
```

### 2. Single-Run Analysis

```bash
python tools/analyze_results.py --results results/phase3_mode_c_adaptive_graph.jsonl
```

### 3. Comparing Modes A, B, and C

```bash
python tools/analyze_results.py --compare \
    results/phase3_mode_a_semantic.jsonl \
    results/phase3_mode_b_fixed_graph.jsonl \
    results/phase3_mode_c_adaptive_graph.jsonl
```
