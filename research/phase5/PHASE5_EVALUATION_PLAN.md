# Phase 5 Research Evaluation Plan: Stratified Evaluation & Ablation Isolation

**Competition:** Google — The Gemma 4 Developer Agent Competition  
**Research Project:** Adaptive Repository Reasoning for Offline Software-Engineering Agents  
**Target Model:** `gemma-4-31b-it-qat-w4a16-ct` (Quantization-Aware W4A16, Air-Gapped / Offline)  
**Status:** Evaluation Plan & Protocol Specification (Pre-Execution Checkpoint)  

---

## 1. Executive Summary & Core Research Questions

Phase 4 demonstrated preliminary evidence on an 8-task suite that confidence-gated adaptive graph reasoning improves task resolution over semantic search alone ($+25.0\text{ percentage points}$) while reducing graph queries by $87.5\%$ compared with mandatory graph reasoning.

However, an 8-task evaluation suite cannot establish broad statistical significance or generalizability. Phase 5 expands evaluation to a large, stratified benchmark to address the central research question:

> **Under what repository/problem conditions does structural reasoning improve successful patch generation, and how much structural reasoning is necessary?**

### Sub-Questions for Phase 5
1. **Category Boundary**: On which architectural categories does code-graph reasoning yield statistically significant improvements over semantic-only search?
2. **Exploration Cost Trade-off**: At what structural complexity does unconditional graph exploration transition from helpful to harmful (via budget exhaustion)?
3. **Component Isolation**: How much of the compound performance gain in Mode D originates from **Structured Internal State** (Mode C1) versus **Test-Driven Repair** (Mode C2)?

---

## 2. Stratified Task Taxonomy & Benchmark Construction

Phase 5 will sample $N = 64$ to $N = 100$ real-world issues from SWE-bench (Verified/Lite) across 8 explicit architectural categories:

| Category | Description | Primary Structural Challenge | Target Tasks ($N=64$) | Target Tasks ($N=100$) |
|---|---|---|:---:|:---:|
| **1. Self-contained / Local** | Single function/method bug with no external callers affected | Minimal: localized semantic search should suffice | 8 | 12 |
| **2. Caller $\rightarrow$ Callee** | Interface contract changes or argument forwarding bugs | High: requires finding incoming/outgoing caller edges | 8 | 14 |
| **3. Dynamic Dispatch** | Method resolution via kwargs, string lookups, or runtime dispatch | High: semantic search misses indirect calls; needs graph neighbors | 8 | 12 |
| **4. Inheritance & Polymorphism** | Subclass overrides, base class hooks, abstract method implementations | High: requires class hierarchy subgraph inspection | 8 | 12 |
| **5. Registration / Factory** | Plugin registries, metaclass registrations, component lookup tables | Medium-High: requires tracking registration side-effects | 8 | 12 |
| **6. Cross-Module Dependency** | Imports across internal packages where symptoms manifest far from cause | High: requires multi-hop dependency tracking | 8 | 14 |
| **7. Test / Fixture Indirection** | Pytest fixtures, mock setups, parameterization factories | High: requires mapping test fixtures to production code | 8 | 12 |
| **8. Multi-File Behavioral Change** | Coordinated edits across two or more source files | Very High: requires multi-node patch planning and consistency | 8 | 12 |

---

## 3. Evaluated Experimental Configurations

Phase 5 evaluates the complete 6-mode matrix, executing all runs under identical model configurations and air-gapped environments:

```text
                  ┌── Mode A: Semantic Control (No graph)
                  │
                  ├── Mode B: Fixed Graph (Mandatory structural reasoning)
                  │
                  ├── Mode C: Adaptive Graph (Confidence-gated structural reasoning)
Adaptive Graph ───┤
                  ├── Mode C1: Adaptive Graph + Structured Internal State (Open Loop)
                  │
                  ├── Mode C2: Adaptive Graph + Test-Driven Repair (Closed Loop)
                  │
                  └── Mode D: Adaptive Graph + Structured State + Test-Driven Repair
                              (Competition Candidate)
```

### Configuration Specifications

| Mode | Config Path | System Prompt Path | Graph Reasoning | Structured State | Test-Driven Repair |
|---|---|---|:---:|:---:|:---:|
| **Mode A** | [`configs/phase4/mode_a/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase4/mode_a/agent.yaml) | [`prompts/system_mode_a.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/prompts/system_mode_a.md) | Prohibited | No | No |
| **Mode B** | [`configs/phase4/mode_b/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase4/mode_b/agent.yaml) | [`prompts/system_mode_b.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/prompts/system_mode_b.md) | Mandatory | No | No |
| **Mode C** | [`configs/phase4/mode_c/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase4/mode_c/agent.yaml) | [`prompts/system.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/prompts/system.md) | Adaptive | No | No |
| **Mode C1** | [`configs/phase4/mode_c1/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase4/mode_c1/agent.yaml) | [`prompts/system_mode_c1.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/prompts/system_mode_c1.md) | Adaptive | **Yes** | No |
| **Mode C2** | [`configs/phase4/mode_c2/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase4/mode_c2/agent.yaml) | [`prompts/system_mode_c2.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/prompts/system_mode_c2.md) | Adaptive | No | **Yes** |
| **Mode D** | [`configs/phase4/mode_d/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase4/mode_d/agent.yaml) | [`prompts/system_mode_d.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/prompts/system_mode_d.md) | Adaptive | **Yes** | **Yes** |

---

## 4. Execution Protocol & Environmental Invariants

To ensure flawless scientific control across all evaluations:
1. **Air-Gapped Containerization**: All executions run inside an isolated offline container. No external network requests or internet access are permitted.
2. **Fixed Model Checkpoint**: `gemma-4-31b-it-qat-w4a16-ct` loaded locally. Sampling parameters fixed via [`configs/sampling.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/sampling.yaml) (`temp=0.2`, `top_p=0.95`, `top_k=40`).
3. **Enforced Tool Budget**: Maximum 30 tool calls per task. Maximum 600s wall-clock timeout.
4. **Deterministic Harness**: Each task begins with a clean `git checkout` of the pre-bug commit. Test verification executes via automated pytest runner scripts.
5. **Immutable Logging**: All trajectories are recorded directly to JSONL trace logs without post-hoc modification.

---

## 5. Metrics & Multi-Stage Outcome Pipeline

Each evaluation run records metrics across the standardized multi-stage pipeline:

```text
Task Attempt
  ├─ 1. Localization Success (True/False): Did the agent read the ground-truth defective file/symbol?
  ├─ 2. Root-Cause Success (True/False): Did the agent formulate a correct causal hypothesis?
  ├─ 3. Patch Generation Success (True/False): Was the initial patch syntactically and semantically valid?
  ├─ 4. Test Validation Success (True/False): Did the initial patch pass the test harness?
  ├─ 5. Repair Success (True/False/Not Attempted): If failed, did the repair loop produce a passing patch?
  └─ 6. Final Task Resolution (PASS/FAIL): Ground-truth test suite pass without regression.
```

### Measured Quantitative Attributes
* **Resolution Rate**: Percentage of tasks resolved per configuration ($Pass / N$).
* **Tool Call Efficiency**: Total tool calls, semantic searches, and graph queries per task.
* **Graph Trigger Ratio**: Fraction of tasks where adaptive gating triggered structural tools.
* **Exploration Footprint**: Unique files read, files edited, and patch line diff size.
* **Repair Overhead**: Number of repair cycles and elapsed wall-clock execution time.
* **Standardized Failure Taxonomy**: 2D classification (Stage $\times$ Category) for all failed runs.

---

## 6. Statistical Significance & Hypothesis Testing

Given $N \ge 64$ tasks, Phase 5 will apply formal hypothesis testing to evaluate performance differences:

1. **Paired Categorical Comparison (McNemar's Test)**:
   * Evaluate whether the difference in pass/fail outcomes between Mode A and Mode C is statistically significant ($p < 0.05$).
   * Evaluate whether Mode C vs. Mode D demonstrates significant incremental benefit.
2. **Efficiency Comparison (Paired Permutation / Wilcoxon Signed-Rank Test)**:
   * Test whether Mode C uses significantly fewer tool calls than Mode B.
3. **Category-Wise Stratified Analysis**:
   * Calculate odds ratios and confidence intervals per category (Categories 1-8) to verify where structural reasoning provides the highest empirical utility.

---

## 7. Execution Governance & Research Gates

1. **No Infrastructure Creep**: AST indexing, LoRA tuning, or multi-agent architectures must not be introduced until Phase 5 baseline evaluation is complete.
2. **Schema & Prompt Freeze**: All 6 `agent.yaml` configs and system prompts must pass `validate_agent_yaml.py` and `validate_system_md.py` prior to launching runs.
3. **Audit Automation**: Results must be ingested deterministically by `tools/audit_results.py` directly from raw execution JSONL logs.
