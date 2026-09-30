# Authoritative Metric Definitions

**Competition**: Google — The Gemma 4 Developer Agent Competition  
**Scope**: Experimental Evaluation Across All Phases (Phase 1, Phase 2, Phase 3, and Future Phases)  
**Status**: Frozen & Authoritative  

This document provides the standard mathematical and operational definitions for all metrics recorded across SWE agent evaluation runs. These definitions are immutable across phases to ensure strict longitudinal comparability.

---

## 1. Primary Evaluation Metric (The North Star)

### **Patch Success Rate ($R_{success}$)**
The proportion of evaluated benchmark tasks where the agent-generated patch resolves the issue without introducing test regressions.

$$\text{Patch Success Rate} = \frac{N_{\text{resolved}}}{N_{\text{evaluated}}} \times 100\%$$

Where:
- $N_{\text{evaluated}}$: Total number of tasks attempted within the evaluation partition.
- $N_{\text{resolved}}$: Number of tasks satisfying all three criteria:
  1. The pre-patch test failed (or reproduced the reported issue symptom).
  2. The patch applied cleanly to the repository without merge or syntax errors.
  3. The post-patch test suite passed all target assertions and regression checks.

> **Principle**: Patch Success Rate is the sole primary metric. Efficiency metrics (tool calls, latency, patch size) are strictly secondary. An agent variant that uses fewer tool calls or runs faster but achieves lower patch resolution is inferior.

---

## 2. Secondary Metrics (Efficiency & Localization)

### 2.1 Tool Invocation Volume
- **Total Tool Calls ($C_{\text{total}}$)**: Sum of all tool invocations recorded across the task trajectory.
- **Average Tool Calls per Task ($\bar{C}$)**:
  $$\bar{C} = \frac{1}{N} \sum_{i=1}^{N} C_i$$

### 2.2 Repository Reasoning & Structural Context
- **Semantic Searches per Task ($\bar{S}_{\text{sem}}$)**: Average count of `search_similar_code` calls per task.
- **Graph Calls per Task ($\bar{G}$)**: Average count of structural code-graph queries (`get_code_neighbors` + `get_code_subgraph`) per task.
- **Symbols Inspected per Task ($\bar{\sigma}$)**: Average count of distinct class or function symbols explicitly queried via graph tools or targeted AST inspection.

### 2.3 File Surface Area & Diff Magnitude
- **Files Inspected per Task ($\bar{F}_{\text{read}}$)**: Average count of distinct repository source files opened and examined via `read_file`.
- **Files Edited per Task ($\bar{F}_{\text{edit}}$)**: Average count of distinct repository source files modified via `edit_file` or `write_file`.
- **Average Patch Size ($\bar{\Delta}$)**: Average total lines modified (added lines + deleted lines) in the final git patch diff:
  $$\bar{\Delta} = \frac{1}{N} \sum_{i=1}^{N} (\text{lines\_added}_i + \text{lines\_deleted}_i)$$

### 2.4 Validation, Repair & Execution Latency
- **Test Attempts per Task ($\bar{T}_{\text{test}}$)**: Total test runner executions (`run_command pytest ...`) performed before and after patch applications.
- **Repair Attempts per Task ($\bar{R}_{\text{repair}}$)**: Count of secondary or tertiary edit cycles executed following a failed test attempt.
- **Elapsed Wall-Clock Time ($\bar{\tau}$)**: Average duration in seconds from initial issue ingestion to terminal `submit_patch` invocation.

---

## 3. Failure Taxonomy & Rates

Each uncompleted task ($outcome \in \{\text{failure}, \text{error}\}$) is classified into exactly one mutually exclusive failure category:

| Failure Category | Code | Operational Definition |
|---|---|---|
| **Test Failure** | `test_fail` | A patch was applied, but post-patch test execution failed (regression, incomplete fix, or assertion mismatch). |
| **No Edit** | `no_edit` | The agent failed to select or edit any source file within the tool budget, submitting an empty diff. |
| **Budget Exhausted** | `budget_exhausted` | The agent consumed its maximum allocated tool calls (e.g. 30 calls) before reaching a passing patch or terminal submission. |
| **Localization Failure** | `localization_failure` | The agent edited files completely unrelated to the defect subsystem, failing tests. |
| **Patch Error** | `patch_error` | Syntactic breakage, unescaped characters, or malformed diff that broke the build/parser. |
| **Environment Error** | `environment_error` | Missing system dependency, runtime timeout, or container fault outside the agent's control. |
| **Submission Error** | `submission_error` | Harness communication failure or invalid `submit_patch` call structure. |

### Failure Rates
For any category $k$:
$$\text{Rate}_k = \frac{N_{\text{failed}, k}}{N_{\text{evaluated}}} \times 100\%$$
- **Test Failure Rate**: $\frac{N_{test\_fail}}{N_{\text{evaluated}}} \times 100\%$
- **No-Edit Rate**: $\frac{N_{no\_edit}}{N_{\text{evaluated}}} \times 100\%$
- **Budget Exhaustion Rate**: $\frac{N_{budget\_exhausted}}{N_{\text{evaluated}}} \times 100\%$
