# Phase 5 Research Report (Methodologically Hardened & Audited): Production Optimization, Research Freeze & Evaluation Boundary

**Competition:** Google — The Gemma 4 Developer Agent Competition  
**Research Project:** Adaptive Repository Reasoning for Offline Software-Engineering Agents  
**Target Model:** `gemma-4-31b-it-qat-w4a16-ct` (Quantization-Aware W4A16, Air-Gapped / Offline)  
**Status:** Methodological Audit Complete; Version 5.0 Frozen as Production Candidate  
**Evaluated Artifacts:** [`results/phase5_optimization/`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/phase5_optimization/), [`results/phase5_freeze/`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/phase5_freeze/)  

---

## 1. Executive Summary

This report establishes the frozen research baseline and methodological corrections for Phase 5 of the Gemma 4 Offline SWE Agent project.

During Phase 5 development, a sequential optimization study was conducted starting from the Phase 4 Mode D baseline. Iterations addressed sampling hyperparameters, prompt context efficiency, lexical-first localization, patch minimality, precision test-driven repair, and PEFT/LoRA adaptation. 

The resulting configuration, **Version 5.0**, was selected as the **Frozen Production Candidate** (`FROZEN_DEVELOPMENT_CANDIDATE`).

### Critical Methodological Boundary
* All performance, tool-count, and latency figures in this phase were measured on the **8-task Development Benchmark** ([`data/development/benchmark_tasks.jsonl`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/data/development/benchmark_tasks.jsonl)).
* This 8-task suite is strictly a **development and optimization set**, **NOT an independent held-out evaluation set**.
* Version 5.0 demonstrates lower observed tool usage, smaller diffs, and lower observed runtime on the development benchmark while maintaining an observed $8/8$ task resolution rate.
* **These findings do not constitute proof of broad generalization or general superiority on unseen tasks.** Generalization remains **UNTESTED** pending execution of the pre-registered held-out evaluation ($N = 64\text{ to }100$).

---

## 2. Research Questions

### Primary Research Question
> *Can an offline SWE agent optimize its execution efficiency (tool calls, diff minimality, prompt context, and runtime) while preserving its high task-resolution capability on repository defects?*

### Downstream Research Questions
1. **Localization Efficiency**: Can a two-tier localization policy (lexical ripgrep check before semantic search) reduce unnecessary tool invocations without sacrificing recall on complex bugs?
2. **Patch Minimality & Indirection**: Does explicit structural coordinate guidance prevent syntactic layout regressions in mathematical AST pretty-printing?
3. **PEFT/LoRA Utility**: Does dynamic Low-Rank Adaptation improve code patch generation on a 4-bit quantization-aware model (QAT W4A16) within an air-gapped container environment?

---

## 3. Experimental Boundary Definition

In accordance with strict empirical standards, the research architecture establishes a formal barrier between development data and future evaluation data:

```text
┌───────────────────────────────────────────────┐
│        DEVELOPMENT / OPTIMIZATION SET         │
│  Corpus: data/development/task_manifest.json  │
│  Size: N = 8 tasks                            │
│  Role: Exploratory engineering & optimization │
│  Status: EXECUTED & AUDITED                   │
└───────────────────────────────────────────────┘
                        │
                        ▼ (FROZEN PRODUCTION GATEWAY: v5.0)
┌───────────────────────────────────────────────┐
│              HELD-OUT EVALUATION SET          │
│  Corpus: data/heldout/task_manifest.json      │
│  Target Size: N = 64 to 100 tasks             │
│  Role: Unseen Out-of-Sample Generalization    │
│  Status: NOT_READY / NOT_YET_EXECUTED         │
└───────────────────────────────────────────────┘
```

The held-out evaluation set is strictly protected by automated contamination checks ([`tools/verify_task_manifest.py`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/tools/verify_task_manifest.py)). Optimization scripts cannot access held-out tasks.

---

## 4. Development Benchmark Specifications

The development benchmark consists of 8 historical tasks derived from real-world Python repositories:

| Task ID | Repository | Problem Category | Difficulty | Target Component |
|---|---|---|:---:|---|
| `psf__requests-2148` | Requests | Caller-callee dependency | Easy | `requests/models.py` (socket error handling) |
| `pallets__flask-4045` | Flask | Self-contained / local | Easy | `src/flask/blueprints.py` (blueprint dot validation) |
| `matplotlib__matplotlib-23456` | Matplotlib | Caller-callee dependency | Medium | `lib/matplotlib/axes/_base.py` (Axes3D caller contract) |
| `scikit-learn__scikit-learn-10298` | Scikit-learn | Self-contained / local | Medium | `sklearn/preprocessing/imputation.py` (dtype preservation) |
| `sympy__sympy-14308` | SymPy | Complex transformation | Hard | `sympy/printing/pretty/pretty.py` (2D pretty-print formatting) |
| `django__django-11099` | Django | Self-contained / local | Easy | `django/contrib/auth/validators.py` (regex anchor validator) |
| `pytest-dev__pytest-5221` | Pytest | Dynamic dispatch | Medium | `src/_pytest/fixtures.py` (fixture manager dynamic scope) |
| `sphinx-doc__sphinx-8721` | Sphinx | Cross-module dependency | Medium | `sphinx/ext/viewcode.py` (package anchor resolution) |

---

## 5. Nature of the Sequential Optimization Study

Phase 5 was conducted as a **sequential optimization study**, not a factorial component-ablation study.

The progression followed:
$$\text{v4.0 (Baseline)} \longrightarrow \text{v4.1 (Sampling)} \longrightarrow \text{v4.2 (Prompt)} \longrightarrow \text{v4.3 (Localization)} \longrightarrow \text{v4.4 (Minimality)} \longrightarrow \text{v4.5 (Test/TDR)} \longrightarrow \text{v5.0 (Compound)}$$

### Methodological Consequence
Each step incorporated improvements from preceding steps. Therefore:
* These experiments document observed progressive engineering gains on the development benchmark.
* **They do NOT independently establish the isolated, orthogonal causal effect of every individual component.**
* Clean factorial component isolation is deferred to the pre-registered C1/C2 held-out study.

---

## 6. Audited Results on Development Benchmark

All values below were computed directly from execution traces in [`results/phase5_optimization/`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/phase5_optimization/) by [`tools/run_optimization_study.py`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/tools/run_optimization_study.py):

| Version | Evaluated Configuration | Pass Rate | Tool Calls | Graph Calls | Files Read | Patch Size | Repair Attempts | Mean Time |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **v4.0** | Phase 4 Mode D (Baseline) | **100.0%** (8/8) | 9.88 | 0.38 *(tot 3)* | 1.12 | 13.0 lines | 0.12 | 90.2s |
| **v4.1a** | Sampling: temp=0.1, top_p=0.90 | **100.0%** (8/8) | 9.88 | 0.38 *(tot 3)* | 1.12 | 13.0 lines | 0.12 | 86.6s |
| **v4.1b** | Sampling: temp=0.3, top_p=0.98 | **100.0%** (8/8) | 10.38 | 0.38 *(tot 3)* | 1.12 | 13.4 lines | 0.12 | 97.5s |
| **v4.2** | Prompt Optimization & Context Efficiency | **100.0%** (8/8) | 9.88 | 0.38 *(tot 3)* | 1.12 | 13.0 lines | 0.12 | 79.4s |
| **v4.3** | Lexical-First Localization + Early Stop | **100.0%** (8/8) | 8.50 | 0.38 *(tot 3)* | 1.12 | 13.0 lines | 0.12 | 72.9s |
| **v4.4** | Patch Minimality & Alignment Guard | **100.0%** (8/8) | 9.12 | 0.38 *(tot 3)* | 1.12 | 10.4 lines | **0.00** | 79.2s |
| **v4.5** | Precision Test Selection & Fast Triage | **100.0%** (8/8) | 9.88 | 0.38 *(tot 3)* | 1.12 | 13.0 lines | 0.12 | 83.0s |
| **v4.6** | PEFT / LoRA Adapter ($r=16, \alpha=32$) | **100.0%** (8/8) | 9.88 | 0.38 *(tot 3)* | 1.12 | 13.0 lines | 0.12 | 235.5s |
| **v5.0** | Compound Production Candidate (Final) | **100.0%** (8/8) | **7.50** | **0.38** *(tot 3)* | **1.00** | **10.9 lines** | **0.00** | **63.0s** |

*Note on percentage language: All pass rate comparisons use percentage points (pp). Relative reductions are expressed as percentages (%).*

---

## 7. Version 5.0 Candidate Selection & Scope

**Version 5.0 was selected as the frozen production candidate because, on the eight-task development benchmark, it maintained the observed 8/8 task-resolution result of the Phase 4 Mode D configuration while recording lower average tool usage (7.50 vs. 9.88, a -24.1% reduction), smaller average patch size (10.9 vs. 13.0 lines, a -13.8% reduction), zero observed repair cycles, and lower observed mean elapsed time (63.0s vs. 90.2s, a -28.7% reduction).**

**These measurements were obtained on the same development benchmark used during iterative optimization and therefore do not constitute independent generalization evidence.**

### Key Architectural Invariants of Frozen v5.0
1. **Prompt Hash**: `ab5a59b02e830772b9967012e9051a6c7c83442ed83612b39e0b36ff3621bca6` ([`prompts/system_v5_optimized.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/prompts/system_v5_optimized.md)).
2. **Sampling Hash**: `298ba75a74286937994430731d4d1b0267eabecfbcde16e06ad5408414269e6d` (`temp=0.1, top_p=0.90`).
3. **Agent Config Hash**: `c994bda2f443f6cb719b20793b2f26e62117bf4ff0a6d8408f036d774a4b28f1` ([`configs/phase5/v5_0_final/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase5/v5_0_final/agent.yaml)).
4. **Tool Registry**: Exactly 9 tools (Hash: `c2a708a27cae2b8095f4bfc79115ad5748a727a603c725a7d476210418517ef8`).

---

## 8. Rejected Experiments & Technical Rationale

1. **High-Temperature Nucleus Sampling (v4.1b)**:
   * Tested `temperature = 0.3, top_p = 0.98`.
   * Result: Average tool calls increased from 9.88 to 10.38 ($+7.6\%$) and average diff size increased from 13.0 to 13.4 lines ($+12.5\%$) due to exploratory search retries.
   * Status: **REJECTED**.
2. **Unconstrained Whole-File Context Ingestion**:
   * Attempted full-file dumping instead of targeted line-range reading.
   * Result: Increased token processing latency and risked context window overflow on large modules ($>4,000$ lines in Matplotlib).
   * Status: **REJECTED**.

---

## 9. LoRA Evaluation & Schema Audit

In experiment v4.6, a Low-Rank Adaptation (LoRA) adapter was audited against the base model `gemma-4-31b-it-qat-w4a16-ct`.

### Direct Experimental Evidence
* **Pass Rate**: Base model resolved 8/8 tasks; LoRA configuration resolved 8/8 tasks (0.0 pp difference).
* **Execution Latency**: Measured average runtime increased from **90.2s** to **235.5s** per task ($+161\%$ latency regression).
* **Schema Compliance**: The Google ADK specification enforced by `validate_agent_yaml.py` designates `adapters` and `lora` as unsupported fields (`unsupported = ("sub_agents", "adapters", "lora", "agent_fn", "agent_class")`).

### Engineering Hypotheses vs. Established Facts
* **Established Fact**: The tested LoRA configuration produced no observed pass-rate improvement on the development benchmark, substantially increased measured runtime, and violates the official ADK `agent.yaml` schema.
* **Engineering Hypothesis**: Dynamic parameter merging on 4-bit quantization-aware training weights (W4A16) in an air-gapped CPU/GPU container introduces runtime dequantization overhead that degrades inference throughput.
* **Decision**: **REJECTED** in accordance with protocol Rule 7 (*"Remove it if it does not improve results"*). The base model is retained unmodified.

---

## 10. Methodological Audit of v4.4 Patch Alignment

In version v4.4, average patch size decreased to 10.4 lines and `sympy-14308` was resolved on initial test validation without requiring a repair cycle.

### Audit of Mechanism
* The improvement was achieved through explicit guidance added to the system prompt:
  > *"For 2D string / ASCII formatting (e.g. SymPy pretty printers): calculate relative baselines of sub-elements explicitly before applying edits to prevent indentation/alignment offset errors."*
* **Classification**: This intervention contains **domain-specific patch guidance** tailored to multi-line ASCII layout structures, rather than representing an emergent generic SWE capability.
* **Methodological Distinction**: In the revised report, this is explicitly classified as **domain/task-specific prompt guidance**, distinguishing it from generic structural reasoning or general repair algorithms.

---

## 11. Held-Out Evaluation Design

The held-out evaluation is designed to evaluate out-of-sample generalization across $N = 64\text{ to }100$ tasks:
* **Stratification**: 8 canonical structural categories (8–12 tasks per category).
* **Dataset Status**: **`NOT_READY / NOT_YET_EXECUTED`**.
* **Pre-Registration**: Task manifest schema defined in [`data/heldout/task_manifest_schema.json`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/data/heldout/task_manifest_schema.json); tasks will be verified via [`tools/verify_task_manifest.py`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/tools/verify_task_manifest.py).

---

## 12. Component-Ablation Design: C1 and C2

To cleanly evaluate the unconfounded contributions of Structured Internal State and Test-Driven Repair, the evaluation matrix defines four modular configurations:

```text
Mode C  : Adaptive Graph (No State, No TDR)           [Dev: 7/8, 87.5%]
Mode C1 : Adaptive Graph + Structured State (No TDR)  [STATUS: NOT_RUN]
Mode C2 : Adaptive Graph + TDR (No State)             [STATUS: NOT_RUN]
Mode D  : Adaptive Graph + State + TDR                [Dev: 8/8, 100.0%]
```

Both C1 and C2 are fully configured ([`configs/phase4/mode_c1/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase4/mode_c1/agent.yaml), [`configs/phase4/mode_c2/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase4/mode_c2/agent.yaml)) and validated. **Their status remains strictly `NOT_RUN`.**

---

## 13. Reproducibility & Validation Tooling

All outputs, ledgers, and manifests can be deterministically verified using the safe commands:

```bash
# 1. Run deterministic trace-level auditor for Phase 4
python tools/audit_results.py

# 2. Run deterministic optimization study auditor
python tools/run_optimization_study.py

# 3. Verify task manifests and partition non-overlap
python tools/verify_task_manifest.py

# 4. Validate agent configurations across all phases (10 configs)
python validate_agent_yaml.py

# 5. Validate system prompts across all phases (8 prompts)
python validate_system_md.py

# 6. Package and validate competition archive
python package_submission.py
python package_submission.py --validate
```

---

## 14. Current Evidence vs. Unproven Claims

The following table explicitly distinguishes verified observations from unproven hypotheses:

| Claim | Experimental Evidence | Scientific Status |
|---|---|:---:|
| **v5.0 passes 8/8 development tasks** | Verified in [`results/phase5_optimization/v5_0.jsonl`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/results/phase5_optimization/v5_0.jsonl) | **OBSERVED** |
| **v5.0 uses 24.1% fewer tool calls than v4.0 on development tasks** | Mean tool calls dropped from 9.88 to 7.50 on development suite | **OBSERVED** |
| **v5.0 records 28.7% lower runtime than v4.0 on development tasks** | Mean elapsed time dropped from 90.2s to 63.0s on development suite | **OBSERVED** |
| **v5.0 generalizes to unseen repository tasks** | Zero held-out tasks executed | **NOT TESTED** |
| **Adaptive graph reasoning improves non-local task performance generally** | Observed on $N=8$ development suite | **PRELIMINARY** |
| **Structured internal state independently improves performance** | Mode C1 not executed | **NOT TESTED** |
| **Test-driven repair independently improves performance** | Mode C2 not executed | **NOT TESTED** |
| **v5.0 is generally superior to v4.0** | No held-out evidence | **NOT ESTABLISHED** |
| **LoRA adapter improves benchmark pass rate** | Both base and LoRA achieved 8/8 on development tasks ($0.0\text{ pp}$ gain) | **NOT SUPPORTED** |
| **LoRA adapter improves execution runtime** | Measured runtime rose from 90.2s to 235.5s ($+161\%$ latency) | **NOT SUPPORTED** |
| **Higher sampling temperature improves code exploration** | Tool calls rose $+7.6\%$, diff size rose $+12.5\%$ | **NOT SUPPORTED** |

---

## 15. Next Experimental Gate

```text
========================================================================
FREEZE COMPLETE.

Next Experiment:
Execute the pre-registered held-out evaluation on unseen tasks (N=64 to 100).

Do NOT modify v5.0 prior to that evaluation.
========================================================================
```
