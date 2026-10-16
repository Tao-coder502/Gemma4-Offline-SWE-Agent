# Held-Out Generalization Evaluation Protocol

**Version**: v1.0 (Pre-Registered Prior to Evaluation)  
**Frozen Agent**: v5.0 (`system_v5_optimized.md`, SHA-256: `ab5a59b0...`)  
**Sampling Config**: `configs/sampling.yaml` (`temp=0.1`, `top_p=0.90`)  
**Protocol Status**: PRE-REGISTERED — no held-out tasks have been observed by the agent or used in prompt tuning.

---

## 1. Purpose

The development benchmark (N=8) was used exclusively for systematic ablation. This protocol defines the pre-registered methodology for evaluating the frozen v5.0 agent on structurally novel, unseen tasks. No agent parameter (prompt, sampling, tool registry) may be modified after reading any held-out task.

---

## 2. Task Stratification

Held-out tasks are selected to **deliberately stress-test the four known risk factors** identified in the development benchmark failure taxonomy:

| Stratum | Category | Stress-Test Target | Target N |
|:---:|---|---|:---:|
| **H1** | Dynamic dispatch / registration hooks | Agent must trace `get_code_neighbors` chains for non-obvious entry points | 8-10 |
| **H2** | Caller regression (multi-module API change) | Agent must proactively inspect downstream callers | 8-10 |
| **H3** | Large, unfamiliar repositories (>50k LOC) | Tests two-tier localization under scale; no pre-training familiarity | 8-10 |
| **H4** | Multi-file coordination (>2 files changed) | Tests context boundary handling; requires multi-file patch plan | 6-8 |
| **H5** | C-extension boundary / metaprogramming | Agent must degrade gracefully (AST limitation acknowledged) | 4-6 |
| **H6** | General cross-language (JS/TS via Tree-sitter) | Tests language-agnostic localization claims | 4-6 |

**Total target**: 38-50 tasks across 6 strata.

---

## 3. Task Selection Rules

1. All tasks sourced from genuine, public SWE-bench repositories. No synthetic or mock instances.
2. Repositories **not present in the development benchmark** (excludes: requests, flask, sympy, matplotlib, pytest, scikit-learn, astropy, sphinx).
3. Tasks must have a confirmed PASS/FAIL ground truth from the official SWE-bench evaluation harness.
4. Stratum H3 repositories selected from packages with minimal occurrence in common LLM pre-training datasets (measured by GitHub star count recency and package age post-2023).

---

## 4. Evaluation Procedure

```
1. Verify agent SHA-256 matches frozen manifest (V5_FREEZE_MANIFEST.json).
2. Load task_manifest.json (to be generated and locked before execution).
3. For each task:
   a. Mount repository snapshot in sandbox (/workspace).
   b. Run agent with frozen prompt + sampling config.
   c. Record: tool_calls, runtime_s, patch_diff, exit_status.
   d. Run SWE-bench verifier: PASS / FAIL / NO_EDIT.
4. Aggregate by stratum. Compute stratum-level and overall pass rates.
5. Report Wilson 95% CI for overall pass rate.
6. Commit full execution trace to results/heldout_evaluation/.
```

---

## 5. Pre-Declared Success Criteria

Results are reported honestly regardless of outcome. The following thresholds are declared **prior to evaluation**:

| Outcome | Interpretation |
|---|---|
| Overall pass rate >= 75% | Generalizes well; architecture claims substantially validated |
| Overall pass rate 55-74% | Partial generalization; development benchmark overfitting present but bounded |
| Overall pass rate < 55% | Significant overfitting; limitations section is the correct framing |
| Stratum H5 pass rate < 30% | Expected; AST limitation correctly documented and observed |
| Stratum H3 pass rate >= 60% | Two-tier localization is scale-robust |

---

## 6. Known Biases to Report

- **Pre-training corpus overlap**: Development benchmark repositories (Flask, Requests, Pytest) are likely well-represented in Gemma 4 pre-training data. Held-out strata H3 and H4 are selected to minimize this effect.
- **Budget headroom proxy**: The development benchmark average of 7.50 tool calls (75% headroom) provides a *structural* (not empirical) argument for generalization capacity. The held-out results will test whether this headroom is actually consumed by harder tasks.
- **Static hardware assumptions**: All runtime figures assume the competition container hardware specification. Results may vary on different GPU configurations.

---

## 7. Execution Lock

> WARNING: THIS FILE IS THE PRE-REGISTRATION RECORD.  
> Any modification to this file after held-out tasks are read constitutes protocol violation and must be disclosed.  
> Execution log will be committed to results/heldout_evaluation/ with an immutable SHA-256 manifest.
