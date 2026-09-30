# Benchmark Task Dataset Specifications

**Status**: Standardized for Arbitrary N Evaluations ($N = 8, 20, 50, 100+$)  
**File Format**: JSON Lines (`.jsonl`) — one JSON object per line.

---

## 1. Schema Definition

Each line in a benchmark task dataset must be a valid JSON object matching the following structure:

```json
{
  "task_id": "psf__requests-2148",
  "repo": "/workspace",
  "issue": "socket.error: [Errno 10054] An existing connection was forcibly closed by the remote host is not caught when streaming responses.",
  "test_cmd": "pytest tests/test_requests.py -k test_response_stream",
  "pass_regex": "passed",
  "category": "caller-callee dependency",
  "difficulty": "medium"
}
```

### Field Definitions

| Field | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | **Yes** | Unique identifier for the benchmark task (e.g. `<repo>__<issue-id>`). |
| `repo` | string | **Yes** | Root filesystem path to the target repository under test. |
| `issue` | string | **Yes** | Complete problem statement / issue description as presented to the agent. |
| `test_cmd` | string | **Yes** | Command executed to run the targeted test suite before and after patching. |
| `pass_regex` | string | *Optional* | Regular expression pattern matched against test stdout/stderr to detect passing tests. |
| `category` | string | *Optional* | Repository reasoning requirement taxonomy (e.g., `self-contained`, `caller-callee`, `dynamic dispatch`). |
| `difficulty` | string | *Optional* | Task difficulty estimation (`easy`, `medium`, `hard`). |

---

## 2. Supported Task Sizes & Batching

The evaluation runner (`tools/run_baseline.py`) natively supports arbitrary task set sizes without modifying code:

```bash
# Evaluate full dataset (e.g. N = 100)
python tools/run_baseline.py \
    --tasks data/benchmark_100.jsonl \
    --results results/phase3_eval_100.jsonl \
    --mode adaptive_graph

# Evaluate a slice (e.g. first 20 tasks)
python tools/run_baseline.py \
    --tasks data/benchmark_100.jsonl \
    --results results/phase3_eval_20.jsonl \
    --mode adaptive_graph \
    --limit 20
```

---

## 3. Repository Reasoning Requirement Categories

When categorizing tasks for structural evaluation, use the standard taxonomy:
1. `self-contained/local`: Defect and fix reside entirely within an isolated leaf function.
2. `caller-callee dependency`: Modifying a method requires understanding caller contracts or return signatures.
3. `cross-module dependency`: The defect requires coordinating changes or contracts across module boundaries.
4. `dynamic dispatch`: Method lookup occurs via decorators, runtime registries, or plugin mechanisms.
5. `inheritance`: Defect depends on base class virtual method behaviors or mixin hierarchies.
6. `registration/factory`: Defect involves central factory mapping or type registration.
7. `complex transformation`: Multi-line AST manipulation, formatting, or compiler/parser passes.
