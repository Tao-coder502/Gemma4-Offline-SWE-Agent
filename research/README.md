# Research: Adaptive Repository Reasoning for Offline SWE Agents

**Competition:** Google — The Gemma 4 Developer Agent Competition  
**Project:** Adaptive Repository Reasoning for Offline Software-Engineering Agents  
**Target Model:** `gemma-4-31b-it-qat-w4a16-ct` (Quantization-Aware W4A16, Air-Gapped / Offline)  

---

## 1. Current Research Status

```text
========================================================================
CURRENT RESEARCH CHECKPOINT: PHASE 5 RESEARCH FREEZE & BOUNDARY LOCK
========================================================================
- Phase 4 Controlled Evaluation:      AUDITED AND COMPLETE
- Phase 5 Development Optimization:   COMPLETE
- Production Candidate (v5.0):        FROZEN (results/phase5_freeze/V5_FREEZE_MANIFEST.json)
- 8-Task Benchmark:                   DEVELOPMENT / OPTIMIZATION SET ONLY
- Held-Out Evaluation (N=64 to 100):  NOT YET EXECUTED (Status: NOT_READY)
- Mode C1 Component Ablation:         NOT_RUN (Infrastructure Ready)
- Mode C2 Component Ablation:         NOT_RUN (Infrastructure Ready)
- Broad Generalization Evidence:      NOT YET ESTABLISHED
========================================================================
```

---

## 2. What Is Being Investigated?

This research investigates whether an offline, air-gapped software-engineering agent can use **adaptive code-graph reasoning** to improve bug resolution while preventing exploration overhead compared with semantic-only search or always-on, mandatory graph exploration.

### Central Research Question
> *Does adaptive use of repository structure and code graphs improve SWE-agent patch success while reducing unnecessary exploration compared with semantic-only or always-on graph reasoning?*

---

## 3. Experimental Configurations

The system defines four standardized, reproducible experimental modes evaluated under identical runtime conditions, tool budgets, and sampling parameters:

| Mode | Designation | Available Tools | Graph Policy | Description |
|---|---|---|---|---|
| **Mode A** | Semantic Control | 7 tools (no graph) | Prohibited | Exact search (`rg`, `grep`) + vector semantic search (`search_similar_code`). |
| **Mode B** | Fixed Graph | 9 tools (full suite) | Mandatory | Unconditionally queries `get_code_neighbors` or `get_code_subgraph` on every candidate symbol. |
| **Mode C** | Adaptive Graph | 9 tools (full suite) | Adaptive | Confidence-gated: invokes graph tools only when semantic localization reveals ambiguous caller/callee or hierarchy relationships. |
| **Mode D** | Phase 4 Compound | 9 tools (full suite) | Adaptive + Closed-Loop | Adaptive graph reasoning + 11-slot Structured Internal State + bounded closed-loop Test-Driven Repair (max 3 cycles). |
| **v5.0** | **Production Candidate** | 9 tools (full suite) | Two-Tier + Adaptive | Two-tier lexical-first localization, patch minimality, early stopping, and fast traceback TDR. **FROZEN**. |

### Planned Modular Ablations
* **Mode C1 (Planned / `NOT_RUN`)**: Mode C + Structured Internal State (open loop).
* **Mode C2 (Planned / `NOT_RUN`)**: Mode C + Test-Driven Repair loop without structured state.

---

## 4. Development Findings vs. Unproven Generalization

### What Has Been Demonstrated on the Development Benchmark ($N=8$)?
1. **Adaptive Graph Reasoning on Non-Local Tasks**:
   * Mode C achieved $7/8$ ($87.5\%$) compared to Mode A's $5/8$ ($62.5\%$), a difference of $+25.0\text{ percentage points (pp)}$.
   * Structural neighbors resolved indirection defects in `matplotlib-23456` and `pytest-5221` where semantic search alone failed.
2. **Exploration Overhead Reduction vs. Fixed Graph**:
   * Mode B executed $24$ total graph queries ($3.00\text{ calls/task}$) and timed out on deep hierarchy traversals (`sphinx-8721`), reaching $6/8$ ($75.0\%$).
   * Mode C triggered graph tools on only $3$ tasks ($0.375\text{ calls/task}$), reducing graph calls by $87.5\%$ while improving resolution by $+12.5\text{ pp}$ over Mode B.
3. **Development Optimization of v5.0**:
   * Version 5.0 maintained the $8/8$ ($100.0\%$) pass rate on the development benchmark while reducing tool calls by $-24.1\%$ (7.50 vs 9.88), reducing patch size by $-13.8\%$ (10.9 vs 13.0 lines), and reducing mean runtime by $-28.7\%$ (63.0s vs 90.2s).

### What Remains Unproven?
1. **Broad Generalization**:
   The eight-task suite is strictly a development benchmark. Generalization across unseen tasks requires validation on the held-out benchmark ($N \ge 64$).
2. **Independent Contributions of State vs. TDR**:
   Modes C1 and C2 remain `NOT_RUN`. Their independent, unconfounded contributions will be evaluated during the held-out evaluation phase.
3. **Multi-File and Cross-Language Generalization**:
   Performance on complex multi-file edits and non-Python stacks remains untested.

---

## 5. Dataset Boundary & Contamination Protection

The repository maintains an explicit barrier between development data and held-out evaluation data ([`research/phase5/EXPERIMENT_BOUNDARY.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/research/phase5/EXPERIMENT_BOUNDARY.md)):
* `data/development/`: 8 development tasks (`task_manifest.json`, `benchmark_tasks.jsonl`).
* `data/heldout/`: Pre-registered held-out task schema (`task_manifest_schema.json`, status: `NOT_READY`).
* Contamination guard in `tools/verify_task_manifest.py` prevents optimization workflows from accessing held-out tasks.

---

## 6. How Results Are Deterministically Verified

All results are audited directly from raw immutable trajectory logs using deterministic tools:

```bash
# 1. Run deterministic Phase 4 audit
python tools/audit_results.py

# 2. Run deterministic Phase 5 optimization study
python tools/run_optimization_study.py

# 3. Verify task manifests and dataset separation
python tools/verify_task_manifest.py

# 4. Validate agent configurations across all phases (10 configs)
python validate_agent_yaml.py

# 5. Validate system prompts across all phases (8 prompts)
python validate_system_md.py

# 6. Verify competition packaging
python package_submission.py
python package_submission.py --validate

# 7. Run clean-room end-to-end verification suite
python tools/verify_clean_submission.py
```

---

## 7. Kaggle Paper Track Submission Report

The authoritative research paper is published in:
* **[`paper/PAPER.md`](../paper/PAPER.md)**: *"Adaptive Repository Reasoning for Offline Software Engineering Agents"*
  - Comprehensive 14-section formal report
  - Full architectural & evolutionary Mermaid diagrams
  - 6-condition cross-phase comparison table
  - Detailed failure taxonomy & resolution matrix
  - Pre-registered held-out evaluation protocol and generalization analysis

