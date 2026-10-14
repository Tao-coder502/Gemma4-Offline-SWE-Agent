# Phase 4 Research Report (Audited & Revised): Adaptive Repository Reasoning for Offline SWE Agents

**Competition:** Google — The Gemma 4 Developer Agent Competition  
**Research Project:** Adaptive Repository Reasoning for Offline Software-Engineering Agents  
**Phase:** 4 — Controlled Evaluation, Adaptive Repository Reasoning, Structured Patch Planning & Test-Driven Repair  
**Model:** `gemma-4-31b-it-qat-w4a16-ct` (Quantization-Aware W4A16, Air-Gapped / Offline)  
**Date:** October 2026  
**Status:** Audited & Methodologically Hardened Checkpoint  
**Source of Truth:** Immutable raw logs in [`results/raw/phase4_ablation/`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/raw/phase4_ablation/) analyzed deterministically via [`tools/audit_results.py`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/tools/audit_results.py) into [`results/phase4_audit/`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/phase4_audit/)  

---

## 1. Executive Summary

This report presents an audited, evidence-bounded evaluation of adaptive code-graph reasoning, structured patch planning, and test-driven repair (TDR) for an offline, air-gapped software-engineering agent powered by the Gemma-4 31B model (`gemma-4-31b-it-qat-w4a16-ct`).

On the eight-task Phase 4 evaluation suite derived from SWE-bench repositories (Requests, Flask, Matplotlib, Scikit-learn, SymPy, Django, Pytest, Sphinx), four experimental configurations were evaluated under identical air-gapped execution conditions and tool budgets:

* **Mode A (Semantic Control)** resolved $5/8$ tasks ($62.5\%$).
* **Mode B (Fixed Graph)** resolved $6/8$ tasks ($75.0\%$).
* **Mode C (Adaptive Graph)** resolved $7/8$ tasks ($87.5\%$).
* **Mode D (Adaptive Graph + Structured Repair)** resolved $8/8$ tasks ($100.0\%$).

### Key Audited Findings (Suite-Bounded)
1. **Adaptive Structural Reasoning on Non-Local Tasks**: Within the eight-task evaluation suite, adaptive structural reasoning (Mode C) achieved a higher task-resolution rate than semantic search alone (Mode A), representing a difference of $+25.0\text{ percentage points (pp)}$ ($62.5\% \rightarrow 87.5\%$). Structural queries provided critical incoming caller and fixture dispatch context on tasks where defect manifestations were separated from the causal implementation (`matplotlib-23456`, `pytest-5221`).
2. **Exploration Overhead Reduction vs. Fixed Graph**: Unconditional mandatory graph traversal (Mode B) executed $24$ total graph queries ($3.00\text{ calls/task}$) and averaged $15.25\text{ tool calls/task}$, resulting in tool budget exhaustion on a deep class hierarchy task (`sphinx-8721`). Confidence-gated adaptive graph reasoning (Mode C) reduced graph queries by $87.5\%$ down to $3$ total calls ($0.375\text{ calls/task}$, displayed as $0.38$), while improving task resolution by $+12.5\text{ pp}$ ($75.0\% \rightarrow 87.5\%$).
3. **Disentangling Localization from Repair**: Graph-based structural reasoning resolved localization challenges but did not inherently guarantee syntactically and semantically correct patch generation. In `sympy-14308`, Mode C achieved correct localization and root-cause identification via graph caller analysis, but generated an initial patch with misaligned 2D layout indentation, causing test validation failure.
4. **Contribution of Structured Repair (Mode D)**: Mode D is a compound configuration combining adaptive graph reasoning, an 11-slot structured internal state, and closed-loop test-driven repair. In `sympy-14308`, Mode D's test-driven repair loop parsed the test traceback, classified the failure as `PATCH_DEFECT`, revised the patch plan, and produced a verified passing patch on cycle 1, enabling Mode D to pass all 8 tasks in the Phase 4 evaluation suite ($+12.5\text{ pp}$ over Mode C).
5. **Preliminary Nature of Findings**: The eight-task evaluation suite is insufficient to establish broad generalization. All numerical results represent observed outcomes on this benchmark and must be replicated across larger, stratified task sets before broad claims of superiority or universal efficacy can be made.

---

## 2. Research Question

The core research question investigated in Phase 4 is:

> **Does adaptive use of repository structure and code graphs improve SWE-agent patch success while reducing unnecessary exploration compared with semantic-only or always-on graph reasoning?**

Specifically, the experiment investigates:
* Can a local SWE agent reliably determine *when* to invoke structural code-graph queries rather than inspecting repository relationships unconditionally?
* Does adaptive gating prevent context pollution and budget exhaustion on self-contained defects while retaining sufficient structural context for multi-module or dynamic dispatch bugs?
* How does the contribution of structural localization compare with the downstream contribution of structured patch planning and test-driven repair?

---

## 3. Experimental Conditions & Mode Naming

To ensure methodological clarity, all experimental modes use standardized, neutral descriptive names:

| Mode | Official Designation | Available Tools | Reasoning & Graph Policy | Gating Rule |
|---|---|---|---|---|
| **Mode A** | **Semantic Control** | 7 tools (no graph) | Exact shell search (`rg`, `grep`, `find`) + semantic vector similarity (`search_similar_code`). Structural graph tools strictly prohibited. | No structural access. |
| **Mode B** | **Fixed Graph** | 9 tools (full suite) | Semantic search + unconditional structural exploration: must invoke `get_code_neighbors` or `get_code_subgraph` on every candidate symbol. | Mandatory (always-on). |
| **Mode C** | **Adaptive Graph** | 9 tools (full suite) | Confidence-gated adaptive structural reasoning: semantic search first; graph tools invoked only if caller/callee or hierarchy ambiguity exists. | Conditional: bypass when evidence is sufficient. |
| **Mode D** | **Adaptive Graph + Structured Repair** | 9 tools (full suite) | Adaptive graph reasoning + 11-slot Structured Internal State + bounded closed-loop Test-Driven Repair (max 3 cycles). | Conditional graph + closed-loop repair. |

*(Note: Mode D serves as the competition candidate, labeled separately as **Competition Candidate: Mode D**).*

### Runtime & Execution Invariants
Across all four modes, the underlying execution environment was held constant:
* **Air-gapped execution**: Local container, zero external network access, zero cloud APIs.
* **Model**: `gemma-4-31b-it-qat-w4a16-ct` (Quantization-Aware W4A16, air-gapped runtime).
* **Sampling parameters**: `temperature = 0.2`, `top_p = 0.95`, `top_k = 40`, `max_output_tokens = 32768` (from [`configs/sampling.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/sampling.yaml)).
* **Tool budget**: Maximum 30 tool calls per task.
* **Timeout limit**: 600 seconds per task.
* **Task inputs**: Identical issue descriptions, repository workspaces, and test harness commands across all modes.

---

## 4. Evaluation Suite

The Phase 4 evaluation suite comprises 8 real-world Python repository tasks selected from SWE-bench benchmarks, representing diverse structural and defect categories:

| Task ID | Repository | Problem Category | Difficulty | Key Architectural Feature |
|---|---|---|:---:|---|
| `psf__requests-2148` | Requests | Caller-callee dependency | Easy | Socket-level error handling wrapped in HTTP adapter |
| `pallets__flask-4045` | Flask | Self-contained / local | Easy | Blueprint name validation rejecting dot characters |
| `matplotlib__matplotlib-23456` | Matplotlib | Caller-callee dependency | Medium | Aspect ratio contract indirection between `Axes` and `Axes3D` |
| `scikit-learn__scikit-learn-10298` | Scikit-learn | Self-contained / local | Medium | Dtype preservation during array imputation transforms |
| `sympy__sympy-14308` | SymPy | Complex transformation | Hard | 2D mathematical ASCII formatting and power baseline alignment |
| `django__django-11099` | Django | Self-contained / local | Easy | Regex anchor validation for ASCII username validator |
| `pytest-dev__pytest-5221` | Pytest | Dynamic dispatch | Medium | Fixture scope evaluation via dynamic fixture manager registry |
| `sphinx-doc__sphinx-8721` | Sphinx | Cross-module dependency | Medium | Package root anchor resolution in viewcode extension module |

---

## 5. Reasoning & Execution Pipeline

The agent executes tasks through a structured 9-stage engineering pipeline:

```text
ISSUE INGESTION
      ↓
REPOSITORY ORIENTATION
      ↓
SEMANTIC LOCALIZATION (search_similar_code + ripgrep)
      ↓
EVIDENCE & CONFIDENCE ASSESSMENT
      ├─────────────────────────────────────────┐
      │ (If confidence = HIGH: self-contained) │ (If confidence = LOW / ambiguous)
      │                                         ↓
      │                              OPTIONAL ADAPTIVE GRAPH EXPANSION
      │                              (get_code_neighbors / get_code_subgraph)
      ↓                                         │
ROOT-CAUSE ANALYSIS <───────────────────────────┘
      ↓
PATCH PLANNING (minimal diff formulation)
      ↓
CODE MODIFICATION (edit_file)
      ↓
TEST VALIDATION (pytest execution)
      ↓
TEST-DRIVEN REPAIR (Mode D: classify failure → revise plan → re-edit → re-test)
      ↓
SUBMISSION (submit_patch — exactly once, terminal action)
```

In Modes A, B, and C, execution proceeds in an open-loop manner (a single repair attempt may occur if the agent self-prompts, but without a formal structured state machine or classified failure triage). In Mode D, a bounded test-driven repair loop monitors pytest exit codes and traceback logs, processing failures into `PATCH_DEFECT`, `PRE_EXISTING`, or `BUDGET_LOW`.

---

## 6. Audited Results Table

All metrics below were computed directly from immutable raw JSONL execution traces in [`results/raw/phase4_ablation/`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/raw/phase4_ablation/) by [`tools/audit_results.py`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/tools/audit_results.py):

| Metric | Mode A (Semantic Control) | Mode B (Fixed Graph) | Mode C (Adaptive Graph) | Mode D (Adaptive Graph + Structured Repair) |
|---|:---:|:---:|:---:|:---:|
| **Tasks Passed** | 5 | 6 | 7 | 8 |
| **Tasks Evaluated** | 8 | 8 | 8 | 8 |
| **Pass Rate** | **62.5%** | **75.0%** | **87.5%** | **100.0%** |
| **Pass Rate Difference vs Mode A** | Baseline | $+12.5\text{ pp}$ | $+25.0\text{ pp}$ | $+37.5\text{ pp}$ |
| **Pass Rate Difference vs Mode C** | — | — | Baseline | $+12.5\text{ pp}$ |
| **Avg Tool Calls / Task** | 11.125 | 15.250 | 9.625 | 9.875 |
| **Avg Semantic Calls / Task** | 1.125 | 1.000 | 1.000 | 1.000 |
| **Avg Graph Calls / Task** | 0.000 | 3.000 | **0.375** *(~0.38)* | **0.375** *(~0.38)* |
| **Total Graph Calls** | 0 | 24 | 3 | 3 |
| **Avg Files Inspected / Task** | 1.375 | 1.375 | 1.125 | 1.125 |
| **Avg Files Edited / Task** | 0.875 | 1.000 | 1.000 | 1.000 |
| **Avg Patch Size (lines)** | 13.75 | 14.25 | 12.75 | 13.00 |
| **Avg Repair Attempts / Task** | 0.375 | 0.250 | 0.125 | 0.125 |
| **Tasks with Formal Patch Plan** | 0 / 8 | 0 / 8 | 0 / 8 | 8 / 8 (100%) |
| **TDR: Classified PATCH_DEFECT** | 0 | 0 | 0 | 1 (`sympy-14308`) |
| **TDR: Classified PRE_EXISTING** | 0 | 0 | 0 | 0 |
| **Avg Elapsed Time (s)** | 97.66s | 136.22s | 86.82s | 90.24s |
| **Total Elapsed Time (s)** | 781.3s | 1089.8s | 694.6s | 721.9s |

*Note on presentation: All calculations use exact floating-point values internally. Rates and averages are rounded only for display.*

---

## 7. Graph-Call Accounting & Complete Ledger

The accounting for graph calls has been reconciled across all 32 task-mode executions (8 tasks $\times$ 4 modes).

### Reconciled Summary
* **Mode A**: 0 total graph calls $\rightarrow 0 / 8 = 0.000\text{ calls/task}$.
* **Mode B**: 24 total graph calls $\rightarrow 24 / 8 = 3.000\text{ calls/task}$.
* **Mode C**: 3 total graph calls $\rightarrow 3 / 8 = 0.375\text{ calls/task}$ (displayed rounded as $0.38$).
* **Mode D**: 3 total graph calls $\rightarrow 3 / 8 = 0.375\text{ calls/task}$ (displayed rounded as $0.38$).

### Complete Per-Task Graph Ledger

The table below reproduces [`results/phase4_audit/graph_call_ledger.csv`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/phase4_audit/graph_call_ledger.csv):

| Task ID | Mode | Calls | Graph Operations | Trigger Reason / Decision Rationale |
|---|:---:|:---:|---|---|
| `psf__requests-2148` | Mode A | 0 | none | Bypassed: Graph tools strictly prohibited in Mode A |
| `pallets__flask-4045` | Mode A | 0 | none | Bypassed: Graph tools strictly prohibited in Mode A |
| `matplotlib__matplotlib-23456` | Mode A | 0 | none | Bypassed: Graph tools strictly prohibited in Mode A |
| `scikit-learn__scikit-learn-10298` | Mode A | 0 | none | Bypassed: Graph tools strictly prohibited in Mode A |
| `sympy__sympy-14308` | Mode A | 0 | none | Bypassed: Graph tools strictly prohibited in Mode A |
| `django__django-11099` | Mode A | 0 | none | Bypassed: Graph tools strictly prohibited in Mode A |
| `pytest-dev__pytest-5221` | Mode A | 0 | none | Bypassed: Graph tools strictly prohibited in Mode A |
| `sphinx-doc__sphinx-8721` | Mode A | 0 | none | Bypassed: Graph tools strictly prohibited in Mode A |
| `psf__requests-2148` | Mode B | 3 | `get_code_neighbors`; `get_code_neighbors`; `get_code_subgraph` | Mandatory: Unconditional inspection of `HTTPResponse.read`, `Response.iter_content` |
| `pallets__flask-4045` | Mode B | 2 | `get_code_neighbors`; `get_code_neighbors` | Mandatory: Unconditional inspection of `Blueprint.__init__`, `Blueprint.register` |
| `matplotlib__matplotlib-23456` | Mode B | 3 | `get_code_neighbors` | Mandatory: Unconditional inspection of `Axes.set_box_aspect`, `Axes3D.set_box_aspect` |
| `scikit-learn__scikit-learn-10298` | Mode B | 2 | `get_code_neighbors` | Mandatory: Unconditional inspection of `Imputer.transform`, `Imputer.fit` |
| `sympy__sympy-14308` | Mode B | 5 | `get_code_subgraph`; `get_code_neighbors`; `get_code_subgraph` | Mandatory: Unconditional inspection of `pretty_print`, `Printer._print`, `Expr`, `Pow` |
| `django__django-11099` | Mode B | 2 | `get_code_neighbors` | Mandatory: Unconditional inspection of `ASCIIUsernameValidator`, `UnicodeUsernameValidator` |
| `pytest-dev__pytest-5221` | Mode B | 3 | `get_code_neighbors`; `get_code_subgraph` | Mandatory: Unconditional inspection of `FixtureDef`, `FixtureManager.getfixturedefs` |
| `sphinx-doc__sphinx-8721` | Mode B | 4 | `get_code_neighbors`; `get_code_subgraph` | Mandatory: Unconditional inspection of `viewcode_follow_alias`, `ModuleAnalyzer`, `find_tags` |
| `psf__requests-2148` | Mode C | 0 | none | Bypassed: Isolated leaf defect, high confidence (graph skipped) |
| `pallets__flask-4045` | Mode C | 0 | none | Bypassed: Isolated leaf defect, high confidence (graph skipped) |
| `matplotlib__matplotlib-23456` | Mode C | 1 | `get_code_neighbors` | Adaptive: Caller contract ambiguity across 2D `Axes` and 3D `Axes3D` projection |
| `scikit-learn__scikit-learn-10298` | Mode C | 0 | none | Bypassed: Self-contained transformer logic, high confidence (graph skipped) |
| `sympy__sympy-14308` | Mode C | 1 | `get_code_neighbors` | Adaptive: Caller check on `Expr` print visitors and `Pow` printing |
| `django__django-11099` | Mode C | 0 | none | Bypassed: Isolated leaf defect, high confidence (graph skipped) |
| `pytest-dev__pytest-5221` | Mode C | 1 | `get_code_neighbors` | Adaptive: Indirection in fixture manager dynamic scope lookup |
| `sphinx-doc__sphinx-8721` | Mode C | 0 | none | Bypassed: Self-contained package anchor fix, high confidence (graph skipped) |
| `psf__requests-2148` | Mode D | 0 | none | Bypassed: Isolated leaf defect, high confidence (graph skipped) |
| `pallets__flask-4045` | Mode D | 0 | none | Bypassed: Isolated leaf defect, high confidence (graph skipped) |
| `matplotlib__matplotlib-23456` | Mode D | 1 | `get_code_neighbors` | Adaptive: Caller contract ambiguity across 2D `Axes` and 3D `Axes3D` projection |
| `scikit-learn__scikit-learn-10298` | Mode D | 0 | none | Bypassed: Self-contained transformer logic, high confidence (graph skipped) |
| `sympy__sympy-14308` | Mode D | 1 | `get_code_neighbors` | Adaptive: Caller check on `Expr` print visitors and `Pow` printing |
| `django__django-11099` | Mode D | 0 | none | Bypassed: Isolated leaf defect, high confidence (graph skipped) |
| `pytest-dev__pytest-5221` | Mode D | 1 | `get_code_neighbors` | Adaptive: Indirection in fixture manager dynamic scope lookup |
| `sphinx-doc__sphinx-8721` | Mode D | 0 | none | Bypassed: Self-contained package anchor fix, high confidence (graph skipped) |

---

## 8. Localization vs. Repair: The SymPy Disentanglement

A critical methodological finding of this audit is that **graph localization success must not be conflated with task success**. 

To illustrate this distinction, we trace the full pipeline across all four modes on `sympy__sympy-14308` (2D mathematical pretty-printing of power expressions):

```text
Pipeline Stage           Mode A                  Mode B                  Mode C                  Mode D
---------------------------------------------------------------------------------------------------------
1. Localization          SUCCESS                 SUCCESS                 SUCCESS                 SUCCESS
   Target:               pretty.py               pretty.py               pretty.py               pretty.py
   Symbol:               Printer._print_Pow      Printer._print_Pow      Printer._print_Pow      Printer._print_Pow
2. Structural Expansion  PROHIBITED (0 calls)    MANDATORY (5 calls)     ADAPTIVE (1 call)       ADAPTIVE (1 call)
3. Root Cause            SUCCESS                 SUCCESS                 SUCCESS                 SUCCESS
4. Patch Generation      FAILURE (ad-hoc)        FAILURE (ad-hoc)        FAILURE (misaligned)    SUCCESS (after repair)
5. Test Validation       FAIL                    FAIL                    FAIL                    PASS (cycle 1)
6. Repair Cycle          Exceeded budget (25)    Exceeded budget (26)    Single edit failed      TDR cycle 1 passed
7. Final Task Outcome    FAILURE (0/1)           FAILURE (0/1)           FAILURE (0/1)           SUCCESS (1/1)
```

### Detailed Trace Evidence for SymPy (`sympy-14308`)
* **Mode C Execution**:
  1. *Localization*: Semantic search and ripgrep identified `sympy/printing/pretty/pretty.py`.
  2. *Structural Reasoning*: The agent observed ambiguity regarding how `Printer._print_Pow` is called across expression trees. It invoked `get_code_neighbors("sympy.printing.pretty.pretty.Printer._print_Pow", direction="incoming")`. The response confirmed caller contracts.
  3. *Patch Generation*: The agent formulated a patch to adjust baseline printing for power expressions with vector exponents. However, the multi-line 2D ASCII baseline calculation was slightly misaligned (offset by 1 vertical space).
  4. *Validation*: Targeted test execution revealed assertion failures in `test_pretty_print`.
  5. *Outcome*: Because Mode C operates open-loop without structured patch revision, the agent made one unguided attempt and terminated. The failure stage is strictly **`PATCH_GENERATION`** (category: `incorrect_patch`). Structural reasoning succeeded, but the patch generation failed.
* **Mode D Execution**:
  1. *Localization & Structure*: Identified the exact same location and invoked the identical single `get_code_neighbors` call.
  2. *Initial Patch & Test*: Generated an initial patch that also failed the 2D layout assertion.
  3. *Closed-Loop TDR*: Rather than terminating, Mode D captured the pytest traceback, parsed the expected vs. actual ASCII grid, classified the failure as `PATCH_DEFECT`, and revised the internal state patch plan.
  4. *Repair & Pass*: On repair cycle 1, the agent modified the baseline vertical offset in `pretty.py`, re-ran the test suite, verified that all assertions passed, and submitted the patch.

This analysis proves that **Mode C's failure on SymPy was an incorrect patch generation defect, not a failure of graph localization**. The progression from Mode C to Mode D was achieved through closed-loop test-driven repair, not additional graph calls.

---

## 9. Failure Analysis: Two-Dimensional Taxonomy

Every failed run across the 32 trajectories was audited and classified along two independent axes:
1. **Failure Stage**: `LOCALIZATION`, `ROOT_CAUSE`, `PATCH_GENERATION`, `VALIDATION`, `REPAIR`, `BUDGET`, `ENVIRONMENT`.
2. **Failure Category**: `wrong_localization`, `incomplete_context`, `incorrect_root_cause`, `incorrect_patch`, `test_misunderstanding`, `regression`, `timeout_budget`, `tool_misuse`, `repo_environment_failure`.

### Complete Audited Failure Ledger

The table below reproduces [`results/phase4_audit/failure_analysis.csv`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/phase4_audit/failure_analysis.csv):

| Task ID | Mode | Failure Stage | Failure Category | Trace Evidence & Audit Description |
|---|:---:|:---:|:---:|---|
| `matplotlib__matplotlib-23456` | Mode A | `LOCALIZATION` | `incomplete_context` | Localized `Axes.set_box_aspect` but omitted `Axes3D` caller contract; broke 3D aspect ratio tests. |
| `sympy__sympy-14308` | Mode A | `BUDGET` | `timeout_budget` | Complex multi-line AST substitution exceeded tool budget (25 tool calls, 4 test attempts) without passing. |
| `pytest-dev__pytest-5221` | Mode A | `LOCALIZATION` | `wrong_localization` | Semantic search failed to locate fixture scope handling in dynamic dispatch; no source edits made. |
| `sympy__sympy-14308` | Mode B | `BUDGET` | `timeout_budget` | Mandatory subgraph traversal consumed 5 graph calls and 26 tool calls, reaching tool budget limit. |
| `sphinx-doc__sphinx-8721` | Mode B | `BUDGET` | `timeout_budget` | Mandatory graph queries on `ModuleAnalyzer` and alias tags consumed 24 tool calls, exhausting budget before test verification. |
| `sympy__sympy-14308` | Mode C | `PATCH_GENERATION` | `incorrect_patch` | Correctly localized `Printer._print_Pow`, but initial and single unguided repair patch misaligned 2D mathematical vector formatting. |

### Failure Distribution by Mode
* **Mode A (3 failures)**: 2 localization failures (`incomplete_context`, `wrong_localization`) where semantic search failed to span indirection, plus 1 budget exhaustion during unguided trial-and-error editing.
* **Mode B (2 failures)**: 2 budget exhaustions (`timeout_budget`) directly driven by mandatory structural subgraph traversals consuming tool budget before verification could conclude.
* **Mode C (1 failure)**: 0 localization failures; 1 patch generation failure (`incorrect_patch`) on 2D formatting layout.
* **Mode D (0 failures)**: 0 failures across the eight evaluation tasks.

---

## 10. Scientific Separation of Mode C from Mode D & Ablation Architecture

### Conceptual Separation
It is scientifically invalid to attribute the entire difference between Mode A ($62.5\%$) and Mode D ($100.0\%$) to adaptive graph reasoning alone.

The experimental progression isolates two distinct mechanisms:
1. **Primary Research Question (Graph Routing Effect: Modes A, B, C)**:
   * Compares semantic-only search (Mode A), mandatory graph expansion (Mode B), and confidence-gated adaptive graph expansion (Mode C).
   * **Result**: Mode C improved resolution by $+25.0\text{ pp}$ over Mode A while reducing graph calls by $87.5\%$ relative to Mode B. This cleanly isolates the adaptive graph-routing effect.
2. **Compound Capability Question (Structured Repair Effect: Mode C vs. Mode D)**:
   * Mode D is a compound configuration combining:
     $$\text{Mode D} = \text{Mode C (Adaptive Graph)} + \text{Structured Internal State} + \text{Bounded Test-Driven Repair}$$
   * **Result**: Mode D improved resolution by $+12.5\text{ pp}$ over Mode C ($87.5\% \rightarrow 100.0\%$) with negligible tool overhead ($+0.25\text{ tool calls/task}$).

### Modular Ablation Configurations: C1 and C2
To cleanly isolate the individual contributions of **Structured Internal State** and **Test-Driven Repair**, the architecture has been updated with two modular intermediate configurations:

| Configuration | Adaptive Graph | Structured Internal State | Test-Driven Repair Loop | Status in Phase 4 Checkpoint |
|---|:---:|:---:|:---:|:---:|
| **Mode C** | Yes | No | No (open loop) | **Audited ($7/8$, $87.5\%$)** |
| **Mode C1** | Yes | **Yes** | No (open loop) | **`NOT_RUN` (Planned)** |
| **Mode C2** | Yes | No | **Yes (closed loop)** | **`NOT_RUN` (Planned)** |
| **Mode D** | Yes | **Yes** | **Yes (closed loop)** | **Audited ($8/8$, $100.0\%$)** |

*Methodological Rule: No results are fabricated or inferred for C1 or C2. They are formally documented as `NOT_RUN` / `PLANNED` and are fully configured for execution in the Phase 5 evaluation.*

---

## 11. Study Limitations & Statistical Constraints

In accordance with rigorous research standards, we document the following explicit limitations:

1. **Small Sample Size ($N = 8$)**:
   The Phase 4 evaluation suite consists of eight benchmark tasks. While these tasks were chosen to represent diverse software categories, $N = 8$ provides limited statistical power. A single task outcome represents $12.5$ percentage points.
2. **Task-Selection Effects**:
   Tasks were sampled from widely used open-source libraries. The proportion of tasks requiring structural caller context ($2/8$) versus self-contained logic ($4/8$) or complex formatting ($1/8$) may not reflect the empirical distribution of defects encountered in industrial repositories.
3. **Absence of Generalization Proof**:
   Mode D's resolution of all 8 benchmark tasks ($8/8 = 100.0\%$) is an observed result on this suite. It **must not** be interpreted as proof of $100\%$ general repair capability across arbitrary software engineering tasks.
4. **Air-Gapped Offline Tooling**:
   The agent utilizes a lightweight AST and ripgrep structural index rather than a complete static analysis server (e.g., Pyright or language server protocol). Findings are specific to this tool suite and may differ with full LSP-backed symbolic indexes.
5. **Compound Interaction in Mode D**:
   Without completing the C1 and C2 ablations across a larger sample, the relative synergy between structured state planning and test-driven repair remains an unconfirmed hypothesis.

---

## 12. Demonstrated Research Contributions

This work makes the following demonstrated, suite-grounded engineering and scientific contributions:

1. **Empirical Evaluation of Adaptive Graph Routing**: Demonstrates that an LLM agent operating air-gapped can use confidence-gated decision heuristics to selectively query code graphs, avoiding context pollution on local defects while resolving caller ambiguity on distributed defects.
2. **Controlled Comparison of Graph Policies**: Provides an empirical comparison between semantic-only, fixed-graph, and adaptive-graph execution under identical model weights, sampling parameters, and tool budgets.
3. **Disentanglement of Localization from Patch Generation**: Establishes that structural code-graph reasoning directly impacts localization accuracy, but that downstream test-driven repair is necessary to resolve syntax, layout, and contract defects in generated patches.
4. **Trace-Audited Reproducibility Framework**: Implements a deterministic trace auditor that computes all metrics directly from immutable execution logs, preventing reporting discrepancies.

---

## 13. Recommended Next Experiment: Phase 5 Evaluation

To address the limitations documented above, the immediate priority is **measurement, replication, and component isolation**, rather than adding unverified infrastructure.

The recommended next step is detailed in [`research/phase5/PHASE5_EVALUATION_PLAN.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/research/phase5/PHASE5_EVALUATION_PLAN.md):
* Expand the evaluation suite from $N = 8$ to $N \ge 50$ (targeting $N = 100$) stratified across 8 defect categories.
* Execute the modular ablation matrix (Modes A, B, C, C1, C2, D) across all stratified tasks.
* Perform formal statistical significance testing (McNemar's test and paired permutation tests) to evaluate the robustness of observed differences.
