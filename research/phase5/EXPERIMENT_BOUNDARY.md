# Phase 5 Research Experiment Boundary: Development vs. Held-Out Evaluation

**Status:** Enforced Experimental Protocol  
**Principle:** *Optimize on development data. Freeze the candidate. Evaluate on unseen data. Only then draw generalization conclusions.*

---

## 1. Explicit Dataset Boundary

To prevent overfitting, post-hoc rationalization, and benchmark contamination, the project enforces a strict boundary between two distinct data corpora:

```text
┌───────────────────────────────────────────────┐
│        DEVELOPMENT / OPTIMIZATION SET         │
│  Path: data/development/benchmark_tasks.jsonl  │
│  Size: N = 8 tasks                            │
│  Repositories: Requests, Flask, Matplotlib,   │
│                Scikit-learn, SymPy, Django,   │
│                Pytest, Sphinx                 │
│  Status: EXECUTED & AUDITED                   │
│  Allowed Use: Exploratory tuning, prompt      │
│               engineering, tool policy        │
│               iteration, failure triage       │
└───────────────────────────────────────────────┘
                        │
                        ▼ (One-Way Gateway: Freeze Candidate v5.0)
┌───────────────────────────────────────────────┐
│              HELD-OUT EVALUATION SET          │
│  Path: data/heldout/task_manifest.json        │
│  Target Size: N = 64 to 100 tasks             │
│  Stratification: 8 Structural Categories      │
│  Status: NOT_READY / NOT_YET_EXECUTED         │
│  Allowed Use: Pre-registered benchmark run   │
│               ONLY for evaluating the frozen  │
│               v5.0 candidate and C1/C2        │
└───────────────────────────────────────────────┘
```

---

## 2. Inviolable Governance Rules

1. **PROHIBITION OF TUNING ON HELD-OUT DATA**:
   Once held-out evaluation tasks are specified, they MUST NOT be used to tune:
   - System prompts or few-shot examples
   - Sampling parameters (`temperature`, `top_p`, `max_output_tokens`)
   - Adaptive graph gating thresholds or triggering heuristics
   - Tool call budgets or timeout limits
   - Early stopping thresholds
   - Test-driven repair cycle caps
   - Patch minimality guards or diff size limits
   - Category definitions or task difficulty ratings

2. **IMMUTABILITY OF HELD-OUT MANIFEST**:
   Prior to executing held-out evaluation, the task manifest must be digitally signed with a SHA-256 hash. Any post-evaluation modification of the task manifest invalidates the evaluation.

3. **TECHNICAL CONTAMINATION GUARDS**:
   Optimization tooling (such as `tools/run_optimization_study.py` or prompt tuning scripts) must fail immediately if passed a path inside `data/heldout/` or an argument requesting held-out evaluation data.

4. **TERMINOLOGY STANDARD**:
   - Results on `data/development/` must always be referred to as *"development benchmark results"* or *"optimization benchmark results"*.
   - The term *"generalization"* or *"held-out evaluation"* must ONLY be used when referencing data from `data/heldout/` after execution.
