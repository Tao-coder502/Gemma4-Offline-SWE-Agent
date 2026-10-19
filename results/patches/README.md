# Benchmark Task Patches (Audited Execution Outputs)

This directory stores the canonical git diff patches generated and submitted by the agent
during the benchmark evaluation across all 32 benchmark tasks.

Each patch is a unified diff ready to be applied via `git apply <patch_file>` against the
respective base commit pinned in `data/expanded_benchmark_32.jsonl` and `data/benchmark_tasks.jsonl`.
