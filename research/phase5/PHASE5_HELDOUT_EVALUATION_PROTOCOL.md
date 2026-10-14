# Phase 5 Held-Out Evaluation Protocol & Statistical Specification

**Competition:** Google — The Gemma 4 Developer Agent Competition  
**Project:** Adaptive Repository Reasoning for Offline Software-Engineering Agents  
**Target Model:** `gemma-4-31b-it-qat-w4a16-ct` (Offline / Air-Gapped)  
**Evaluated Systems:** Frozen Production Candidate v5.0, Baselines Mode A/B/C/D, Ablations C1/C2  
**Status:** Pre-Registered Protocol Specification (Pre-Execution Freeze)  

---

## 1. Core Research Questions

### Research Question 1 (Generalization of Frozen Production Candidate)
> *Does the frozen v5.0 production candidate maintain task-resolution performance, tool efficiency, and diff minimality when evaluated on previously unseen repository issues?*

### Research Question 2 (Structural Locality Hypothesis)
> *Does adaptive code-graph reasoning provide measurable utility on structurally non-local tasks (caller-callee indirection, dynamic dispatch, inheritance) compared to locally scoped tasks where semantic search suffices?*

### Research Question 3 (Downstream Test-Driven Repair Utility)
> *Does bounded closed-loop test-driven repair improve final patch success on tasks where initial localization is correct but initial patch validation fails?*

### Research Question 4 (Component Isolation: State vs. TDR)
> *What are the independent, unconfounded contributions of Structured Internal State (Mode C1) and Test-Driven Repair (Mode C2) when isolated from compound Mode D?*

---

## 2. Experimental Boundary & Partition Definition

The evaluation enforces a strict, immutable partition between development and held-out corpora:

| Attribute | Development Corpus | Held-Out Evaluation Corpus |
|---|---|---|
| **Location** | [`data/development/task_manifest.json`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/data/development/task_manifest.json) | [`data/heldout/task_manifest.json`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/data/heldout/task_manifest.json) |
| **Sample Size** | $N = 8$ tasks | $N = 64\text{ to }100$ tasks (Target) |
| **Status** | **EXECUTED & AUDITED** | **NOT_YET_EXECUTED / NOT_READY** |
| **Role in Research** | Exploratory optimization, prompt tuning, heuristic design | Strict, one-shot out-of-sample generalization test |
| **Agent Tuning Permitted** | Yes (completed during Phase 5 optimization) | **STRICTLY PROHIBITED** |

---

## 3. Evaluated System Configurations

| Configuration | Designation | Graph Policy | Structured State | TDR Loop | Status |
|---|---|:---:|:---:|:---:|:---:|
| **Mode A** | Semantic Control | Prohibited | No | No | Evaluated on Dev ($5/8$) |
| **Mode B** | Fixed Graph | Mandatory | No | No | Evaluated on Dev ($6/8$) |
| **Mode C** | Adaptive Graph | Adaptive | No | No | Evaluated on Dev ($7/8$) |
| **Mode C1** | Adaptive + State | Adaptive | **Yes** | No | **`NOT_RUN` (Ablation Ready)** |
| **Mode C2** | Adaptive + TDR | Adaptive | No | **Yes** | **`NOT_RUN` (Ablation Ready)** |
| **Mode D** | Phase 4 Compound | Adaptive | **Yes** | **Yes** | Evaluated on Dev ($8/8$) |
| **v5.0** | **Production Candidate** | Two-Tier + Adaptive | **Yes** | **Yes (Fast Triage)** | **FROZEN (Dev: $8/8$)** |

---

## 4. Primary & Secondary Metrics

### Primary Metric
* **Final Patch Success Rate ($R_{pass}$)**:
  $$\text{Numerator: Count of tasks where post-patch tests pass and pre-patch tests failed}$$
  $$\text{Denominator: Total evaluated tasks } N$$
  $$\text{Aggregation: Pooled percentage with Wilson 95% Binomial Score Interval}$$

### Secondary Metrics
1. **Localization Success Rate ($R_{loc}$)**: $\frac{N_{\text{read contains defective symbol}}}{N}$
2. **Root-Cause Success Rate ($R_{rc}$)**: $\frac{N_{\text{hypothesis matches defective cause}}}{N}$
3. **Patch-Generation Success Rate ($R_{patch}$)**: $\frac{N_{\text{valid initial patch generated}}}{N}$
4. **Test-Validation Success Rate ($R_{val}$)**: $\frac{N_{\text{initial patch passes tests}}}{N}$
5. **Repair Success Rate ($R_{repair}$)**: $\frac{N_{\text{repaired and passed}}}{N_{\text{repair attempts triggered}}}$
6. **Tool Usage Efficiency**: Mean and standard deviation of total tool calls per task.
7. **Graph Routing Efficiency**:
   - Graph Trigger Rate: $\frac{N_{\text{graph triggered}}}{N}$
   - Mean Graph Calls / Task: $\frac{\sum \text{graph calls}}{N}$
8. **Patch Minimality**: Mean lines of code modified in git diff per resolved task.
9. **Execution Latency**: Mean elapsed wall-clock seconds per task.

---

## 5. Category Stratification Analysis

The held-out suite samples tasks equally across 8 structural categories (8–12 tasks per category):
1. **Self-contained / local**
2. **Caller $\rightarrow$ callee dependency**
3. **Dynamic dispatch**
4. **Inheritance & polymorphism**
5. **Registration / factory patterns**
6. **Cross-module dependency**
7. **Test / fixture indirection**
8. **Multi-file behavioral change**

### Reporting Rule
For each category, report: $N$, Pass Rate, Localization Rate, Graph Trigger Rate, Mean Graph Calls, Mean Tool Calls, Repair Rate, and Dominant Failure Stages.
*Categorical results must be interpreted as **contextual utility boundaries**, not as a ranking or competition leaderboard.*

---

## 6. Statistical Significance & Hypothesis Testing

1. **Binary Outcome Comparison (Paired McNemar's Test)**:
   Used to test whether difference in pass/fail transitions between paired models (e.g. Mode C vs Mode D, or v4.0 vs v5.0) is statistically significant at $\alpha = 0.05$:
   $$\chi^2 = \frac{(b - c)^2}{b + c}, \quad \text{where } b = \text{Model 1 pass / Model 2 fail}, \quad c = \text{Model 1 fail / Model 2 pass}$$
2. **Continuous Efficiency Comparison (Wilcoxon Signed-Rank Test)**:
   Non-parametric paired comparison for tool calls and elapsed time across identical tasks.
3. **Binomial Confidence Intervals (Wilson Score Interval)**:
   For all success proportions, report Wilson $95\%$ confidence intervals:
   $$w = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

---

## 7. Execution Governance & Stop Gate

1. **NO FURTHER OPTIMIZATION**: The v5.0 candidate is permanently frozen.
2. **NO ACCIDENTAL RUNS**: The held-out benchmark must NOT be launched automatically. Execution is deferred to the formal Phase 5 evaluation phase.
