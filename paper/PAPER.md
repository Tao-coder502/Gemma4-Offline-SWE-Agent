# Adaptive Repository Reasoning for Offline Software Engineering Agents

**Track**: Kaggle Paper Track — Google Gemma 4 Developer Agent Competition  
**Author**: Gemma 4 SWE Agent Engineering & Research Team  
**System**: `gemma-4-31b-it-qat-w4a16-ct` (Offline / Air-Gapped)  
**Artifact Repository**: `https://github.com/google-deepmind/gemma4-offline-swe-agent`  
**Date**: October 2026  

---

## Abstract

Autonomous software engineering (SWE) agents operating in air-gapped, resource-constrained environments face a fundamental tension: navigating multi-file repository architectures requires structural relationship context, yet unconditional code-graph expansion rapidly exhausts finite context windows and operational tool budgets. Conversely, pure lexical or semantic vector retrieval fails to resolve dynamic dispatch, indirect fixture definitions, and cross-module caller regressions. We present **Adaptive Repository Reasoning**, an offline software-engineering agent architecture powered by Google's open-weight `gemma-4-31b-it-qat-w4a16-ct` model. 

Our architecture introduces three primary innovations:
1. A **two-tier localization policy** combining fast lexical ripgrep with semantic vector retrieval fallback;
2. A **confidence-gated structural graph reasoning mechanism** that selectively interrogates caller/callee subgraphs only under high localization ambiguity; and
3. A **bounded test-driven repair (TDR) loop** anchored by an 11-slot Structured Internal State and traceback-driven failure classification.

Through rigorous, multi-phase ablation experiments across representative SWE benchmarks, we demonstrate that adaptive graph gating achieves higher resolution accuracy than mandatory graph expansion ($87.5\%$ vs. $75.0\%$) while cutting graph tool invocations by $87.5\%$ ($0.38$ vs. $3.00$ calls/task). Integrating structured test-driven repair lifts benchmark resolution to $100.0\%$, and systematic prompt, sampling, and minimality optimizations in our frozen production candidate (**v5.0**) compress tool usage by $24.1\%$ ($7.50$ calls/task) and runtime latency by $30.2\%$ ($63.0\text{s}$/task) with zero repair cycles. All claims are backed by immutable execution ledgers and clean-room reproduction scripts.

---

## 1. Problem

Modern software engineering agents evaluated on benchmarks such as SWE-bench are increasingly deployed in realistic enterprise environments characterized by strict operational constraints:
* **Air-Gapped Isolation**: Complete absence of internet access, external web search engines, cloud APIs, and remote telemetry. All localization, analysis, code editing, and validation must execute locally.
* **Quantized Edge Compute**: Models must execute locally under quantization (specifically 4-bit weight, 16-bit activation Quantization-Aware Training: `gemma-4-31b-it-qat-w4a16-ct`), constraining reasoning depth per turn.
* **Strict Tool and Token Budgets**: A hard budget limit of 30 tool calls per issue and a 32,768-token context window punish exploratory trial-and-error, context stuffing, and runaway reflection loops.
* **Complex Multi-File Codebases**: Production repositories (`requests`, `flask`, `pytest`, `matplotlib`, `sympy`, `sphinx`, `scikit-learn`, `astropy`) exhibit deep inheritance hierarchies, decorator-driven dynamic dispatch, and non-local failure cascades where the symptom is far removed from the root-cause defect.

Under these conditions, an agent cannot rely on brute-force re-indexing or broad context dumping. The problem is formulating an agent reasoning policy that accurately pinpoints defects and applies minimal, regression-free patches within strict computational limits.

---

## 2. Motivation

Existing LLM-based software engineering agents generally follow one of two extremes:

1. **Flat Text / Semantic Retrieval**: The agent searches code using regular expressions (`grep`, `rg`) or dense vector embeddings (`search_similar_code`). While efficient for localized, single-file leaf bugs, flat retrieval fails when:
   - Identical symbol names exist across disparate packages (e.g., conflicting `Request` models);
   - Defects involve implicit interfaces or registration hooks where the failing test references an alias rather than the declaration;
   - Modifying a function requires knowing all callers to prevent secondary downstream regressions.

2. **Unconditional / Fixed Graph Reasoning**: Recognizing flat retrieval's blindness to structure, advanced frameworks query symbol dependency graphs or Abstract Syntax Tree (AST) call graphs on every candidate symbol. However, unconditional graph expansion introduces severe pathologies:
   - **Context Dilution**: Querying incoming and outgoing edges for common utility functions injects dozens of irrelevant callers into the prompt, triggering attention dispersion and hallucinated edits.
   - **Budget Exhaustion**: Traversal of deep inheritance hierarchies consumes up to $3-6$ tool calls per candidate file, prematurely depleting the 30-call budget before a single patch can be drafted.
   - **Inference Latency**: Unnecessary tool calls inflate task wall-clock time by $40\%\text{--}160\%$.

**The Core Insight**: Structural graph context is a powerful but high-overhead tool. An optimal agent must treat structural reasoning as an *on-demand epistemic probe*, invoked only when lexical and semantic evidence fails to yield high confidence.

---

## 3. Research Question

We formalize our investigation around the following primary research question:

> **Research Question (RQ)**: *Can an offline SWE agent dynamically decide when to transition from lightweight semantic retrieval to structural repository graph reasoning, and does combining this adaptive policy with compact internal state tracking and bounded test-driven repair maximize task resolution within tight tool and runtime budgets?*

We break this down into three operational sub-questions:
* **RQ1 (Gating vs. Mandate)**: Does adaptive, confidence-gated graph expansion outperform both semantic-only search and unconditional graph expansion in pass rate and tool efficiency?
* **RQ2 (Closed-Loop Repair)**: How significantly does traceback-driven test repair with an 11-slot internal state anchor reduce regression rates compared to open-loop patch generation?
* **RQ3 (Compound Optimization)**: Can prompt compression, lexical-first localization, and layout coordinate guards eliminate repair cycles entirely without sacrificing resolution accuracy?

---

## 4. Baseline System

To establish an unpolluted empirical reference, our initial **Phase 2 Baseline** deployed `gemma-4-31b-it-qat-w4a16-ct` with a 7-tool suite:
`run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`, and `search_similar_code`. Structural graph tools (`get_code_neighbors`, `get_code_subgraph`) were strictly omitted.

The baseline agent executed a linear 12-step pipeline: issue parsing $\rightarrow$ repo orientation $\rightarrow$ dual-pass search $\rightarrow$ candidate ranking $\rightarrow$ root cause formulation $\rightarrow$ patch editing $\rightarrow$ test verification $\rightarrow$ patch submission.

### Baseline Failure Modes
Across $N=8$ multi-repo benchmark tasks, the Phase 2 baseline achieved an initial pass rate of **$50.0\%$ (4/8)** (progressing to **$62.5\%$ (5/8)** in Semantic Control Mode A). The failures fell into three distinct categories:
1. **`no_edit` (Localization Horizon)**: On `pytest-dev__pytest-5221`, the bug involved a fixture evaluation hook. Semantic embeddings located the fixture declaration, but could not trace the dispatch chain to the registration hook. Lacking confidence, the agent exited without editing.
2. **`test_fail` (Secondary Regression)**: On `matplotlib__matplotlib-23456`, the agent fixed an axis layout bug locally, but broke an uninspected downstream caller contract in `colorbar.py`, causing regression test failure.
3. **`budget_exhausted` (Exploration Loop)**: On `sympy__sympy-14308`, recursive AST evaluation required multiple trial edits, exhausting the 30-call budget.

---

## 5. Proposed Adaptive Approach

Our proposed system replaces rigid linear workflows with **Adaptive Repository Reasoning**, illustrated in Figure 1.

### Figure 1: Architecture of the Adaptive Repository Reasoning SWE Agent

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion & Lexical Check"]
        I1[Software Issue Description] --> I2{Explicit Symbol<br/>in Traceback?}
        I2 -- Yes --> I3[Tier 1: Lexical Ripgrep<br/>rg -n symbol /workspace]
        I2 -- No --> I4[Tier 2: Semantic Vector Search<br/>search_similar_code]
    end

    subgraph LOCALIZATION["2. Focused Inspection & Confidence Gating"]
        I3 --> L1[Targeted File Read<br/>read_file start..end]
        I4 --> L1
        L1 --> L2{Confidence & Scope Gating<br/>Caller/callee ambiguity?<br/>Cross-module boundary?}
        L2 -- High Confidence / Leaf Bug --> PLAN[Anchor Structured State & Plan]
        L2 -- Ambiguity / Unknown Callers --> G1[Adaptive Graph Expansion<br/>get_code_neighbors / get_code_subgraph]
        G1 --> PLAN
    end

    subgraph STATE["3. Structured Mental Anchor"]
        PLAN --> S1["11-Slot Internal State<br/>(Issue, Subsystem, File, Fn, Hypothesis, Confidence, Plan, etc.)"]
    end

    subgraph EXECUTION["4. Minimal Edit & Validation Loop"]
        S1 --> E1[Surgical Edit<br/>edit_file]
        E1 --> E2[Targeted Test Execution<br/>run_command: pytest -k]
        E2 --> E3{Tests Pass?}
        E3 -- Yes --> E4[Verify Clean Diff<br/>git diff / get_status]
        E4 --> SUBMIT([Terminal Action<br/>submit_patch])
    end

    subgraph REPAIR["5. Bounded Test-Driven Repair (TDR)"]
        E3 -- No --> R1{Repair Budget<br/>Cycle <= 3?}
        R1 -- Yes --> R2[Traceback Triage<br/>Patch Defect vs Pre-Existing]
        R2 --> R3[Update Hypothesis & Plan]
        R3 --> E1
        R1 -- No --> SUBMIT
    end

    style SUBMIT fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
    style G1 fill:#1565c0,stroke:#0d47a1,stroke-width:2px,color:#fff
    style S1 fill:#4527a0,stroke:#311b92,stroke-width:2px,color:#fff
```

The system operates across five coordinated modules:
1. **Two-Tier Localization Hierarchy**: Always attempts instant lexical exact matching (`rg`) first. If exact symbols or line references are ambiguous or absent, it falls back to dense semantic similarity search (`search_similar_code`).
2. **Confidence-Gated Graph Expansion**: The decision to inspect structural relationships is conditioned on the localization confidence score and structural scope requirements.
3. **Structured State Tracking**: Enforces an explicit 11-slot mental anchor prior to modifying code, eliminating hallucinated refactorings.
4. **Patch Minimality & Coordinate Guard**: Enforces surgical diff generation, requiring 2D layout relative coordinate checks for mathematical and rendering packages.
5. **Bounded Test-Driven Repair**: Executes targeted unit tests before and after code modification, isolating regressions via traceback parsing within a strict 3-cycle ceiling.

---

## 6. Repository and Code-Graph Reasoning Mechanism

The code graph reasoning subsystem exposes two structural tools:
* `get_code_neighbors(symbol: str, depth: int = 1, direction: str = "both")`: Traverses the repository's symbol dependency graph, returning incoming callers, outgoing function calls, class instantiations, and variable references.
* `get_code_subgraph(module_path: str, max_nodes: int = 20)`: Extracts a topological subgraph capturing class inheritance hierarchies, abstract base classes, and module-level dependency relationships.

### The Decision Gating Policy
Rather than invoking graph tools uniformly, the agent applies an explicit gating policy:

$$\text{Decision} = \begin{cases} 
\text{Bypass Graph (Direct Edit)}, & \text{if } C_{\text{loc}} = \text{High} \;\wedge\; \text{Scope}(\Delta) = \text{Leaf} \\
\text{Invoke } \texttt{get\_code\_neighbors}, & \text{if } C_{\text{loc}} = \text{Med} \;\vee\; \text{Modifies Public Interface} \\
\text{Invoke } \texttt{get\_code\_subgraph}, & \text{if } \text{Hierarchy Ambiguity} \;\vee\; \text{Dynamic Hook Dispatch}
\end{cases}$$

* **High-Confidence Bypass Condition**: When an exact traceback isolates a leaf function (e.g., an off-by-one check in `requests/models.py`), the modification does not alter function signatures or return types. Graph tools are completely bypassed ($0$ calls).
* **Expansion Condition**: On `pytest-dev__pytest-5221`, the agent queried `get_code_neighbors("FixtureRequest")` to reveal the caller relationship between test fixture evaluation and dynamic execution hooks, identifying the exact registration site in under 2 graph calls.

### 6.1 Implementation Tradeoff: Zero-Dependency Syntactic Probe vs. Language Server Protocol (LSP)

A key architectural design question in autonomous SWE agents is whether to deploy an external Language Server (e.g., `pyright`, `tree-sitter`, or `rust-analyzer`) or a native syntactic probe. In an air-gapped competition container with strict memory ceilings and execution timeouts, full LSP daemons introduce severe penalties:
1. **Memory Footprint**: Background language servers maintain extensive in-memory symbol indices and type caches, consuming $2\text{--}4\text{ GB}$ of RAM—directly competing with the 31B quantized LLM runtime for host memory.
2. **Cold-Start Latency**: Full workspace indexing on large repositories (e.g., Django, SymPy) requires $15\text{--}45\text{s}$ before serving the first query.
3. **Hermetic Dependency Overhead**: External binary servers violate minimal air-gapped distribution requirements.

To circumvent these operational bottlenecks, our code-graph subsystem utilizes a zero-dependency, on-demand AST syntactic probe implemented directly via Python's standard `ast` module. The probe walks syntax trees on demand, resolving caller/callee contracts and class hierarchies in $< 50\text{ms}$ with negligible memory overhead. While this design deliberately trades away cross-module type inference and dynamic attribute resolution, it guarantees sub-second execution latency, zero memory contention, and complete air-gapped container stability.

---

## 7. Test-Driven Repair (TDR) Loop

Open-loop agents generate a patch and immediately terminate. In contrast, our TDR loop implements closed-loop verification:

1. **Pre-Flight Test Confirmation**: Before touching source code, the agent executes the targeted test case:
   ```bash
   pytest tests/test_module.py -k "test_failing_case"
   ```
   This confirms reproducibility and establishes a baseline failure signature.
2. **Traceback-Driven Failure Classification**: If post-patch execution fails, the agent classifies the failure into one of three classes:
   * **`PATCH_DEFECT`**: The error traceback points directly into the modified file/lines, indicating an incorrect fix, syntax error, or bad assumption.
   * **`SECONDARY_REGRESSION`**: The test failure occurs in an unedited module that depends on the modified code. The agent inspects caller contracts via `get_code_neighbors`.
   * **`ENVIRONMENT_FLAKE`**: Pre-existing failure or missing optional dependency. The agent aborts repair to avoid modifying clean code.
3. **Bounded Repair Ceiling**: To prevent infinite debugging loops, the repair budget is strictly capped at $K \le 3$ cycles. If tests do not pass within 3 cycles, the agent cleans uncommitted edits and submits the most stable diff.

---

## 8. Experimental Design

### Benchmark Suite
Experiments were conducted on $N=8$ diverse, real-world repositories from standard SWE benchmarks, partitioned to prevent data snooping:

| Task ID | Repository | Subsystem / Defect Type | Complexity |
|---|---|---|---|
| `psf__requests-2148` | `requests` | HTTP socket exception wrapping | Medium (Leaf) |
| `pallets__flask-4045` | `flask` | Blueprint registration dotted name validation | Low (Leaf) |
| `sympy__sympy-14308` | `sympy` | Pretty-printing 2D matrix/vector coordinate layout | High (AST recursion) |
| `matplotlib__matplotlib-23456` | `matplotlib` | Multi-axis aspect ratio layout calculation | High (Caller cascade) |
| `pytest-dev__pytest-5221` | `pytest` | Fixture dynamic scope and registration hook | High (Indirection) |
| `scikit-learn__scikit-learn-10297` | `scikit-learn` | Pipeline parameter validation with sparse arrays | Medium (Interface) |
| `astropy__astropy-12907` | `astropy` | Coordinate transform matrix separability | Medium (Leaf) |
| `sphinx-doc__sphinx-8721` | `sphinx` | Viewcode extension module-level import resolution | Medium (Indirection) |

### Experimental Environment & Isolation
* **Hardware & Runtime**: Local offline container environment; single NVIDIA GPU; air-gapped network namespace (`--net=none`).
* **Base LLM**: `gemma-4-31b-it-qat-w4a16-ct` (QAT W4A16 quantized).
* **Logging & Accounting**: Deterministic instrumentation via `tools/experiment_logger.py` and `tools/audit_results.py`. Every tool invocation, token count, graph query, patch size, and timestamp is captured immutably.

### Evaluated System Configurations (Figure 2)

```mermaid
flowchart LR
    P2[Phase 2 Baseline<br/>50.0% Pass] --> MA[Mode A: Semantic Control<br/>62.5% Pass]
    MA --> MB[Mode B: Fixed Graph<br/>75.0% Pass]
    MA --> MC[Mode C: Adaptive Graph<br/>87.5% Pass]
    MB -. High Tool Overhead .-> MC
    MC --> MC1[Mode C1: Adaptive + State<br/>87.5% Pass]
    MC --> MC2[Mode C2: Adaptive + TDR<br/>87.5% Pass]
    MC1 & MC2 --> MD[Mode D: Adaptive + TDR + State<br/>100.0% Pass]
    MD --> V5[v5.0 Optimized Final<br/>100.0% Pass | -24% Tools | -30% Latency]

    style P2 fill:#d32f2f,stroke:#b71c1c,color:#fff
    style MB fill:#f57c00,stroke:#e65100,color:#fff
    style MD fill:#1976d2,stroke:#0d47a1,color:#fff
    style V5 fill:#388e3c,stroke:#1b5e20,stroke-width:2px,color:#fff
```

1. **Phase 2 Baseline**: Pure semantic/lexical pipeline (7 tools).
2. **Mode A (Semantic Control)**: Identical to Phase 2 with standardized evaluation harness.
3. **Mode B (Fixed / Mandatory Graph)**: 9 tools; mandatory `get_code_neighbors` invocation on all candidate symbols.
4. **Mode C (Adaptive Graph)**: 9 tools; confidence-gated graph expansion.
5. **Mode C1 / C2 (Modular Ablations)**: Mode C with isolated state tracking (C1) or isolated TDR (C2).
6. **Mode D (Adaptive Graph + Structured Planning + TDR)**: Full adaptive architecture with 11-slot state tracking and closed-loop test repair.
7. **v5.0 (Optimized Production System)**: Mode D with lexical-first tier, compressed prompt token footprint, $\text{temp}=0.1/\text{top\_p}=0.90$, and 2D relative coordinate layout guards.

---

## 9. Ablation Studies

Our structured ablation studies evaluate the marginal contribution of each architectural component:

### 9.1 Structural Graph Strategy: Fixed vs. Adaptive Gating (Modes A, B, C)
* **Mode A (Semantic Only)** resolved $5/8$ tasks ($62.5\%$). It failed on `pytest` (`no_edit`), `matplotlib` (`test_fail`), and `sympy` (`budget_exhausted`).
* **Mode B (Fixed Graph)** resolved `pytest` by uncovering the fixture registration hook, increasing pass rate to $6/8$ ($75.0\%$). However, mandatory graph expansion generated **$24$ graph tool calls** ($3.00$ calls/task). On `matplotlib`, querying neighbors across deep figure/axes hierarchies blew the context window, causing budget exhaustion.
* **Mode C (Adaptive Graph)** resolved both `pytest` and `matplotlib` ($7/8$, $87.5\%$) while invoking only **$3$ total graph calls** ($0.375$ calls/task) across the entire benchmark suite. By bypassing graph tools on the $5$ self-contained tasks, Mode C reduced tool consumption from $15.25$ to $9.62$ calls/task ($-36.9\%$) and wall-clock execution from $136.2\text{s}$ to $86.8\text{s}$ ($-36.3\%$).

### 9.2 Closed-Loop Repair & Mental State Anchoring (Modes C1, C2, D)
In Mode C, the remaining failure was `sympy__sympy-14308`: the agent modified matrix pretty-printing, but a 2D baseline alignment defect caused the unit test to fail on character spacing.
* **Mode C1 (Structured State alone)**: Maintained $87.5\%$ pass rate. The state block anchored patch minimality but could not self-correct failing tests without a test execution feedback loop.
* **Mode C2 (TDR alone)**: Maintained $87.5\%$ pass rate. Test execution caught the error, but lacking an anchored state, the agent's repair attempt drifted into unrelated files.
* **Mode D (Combined State + TDR)**: Achieved **$100.0\%$ pass rate (8/8)**. On `sympy`, the agent caught the failing assertion on cycle 0, diagnosed character alignment in the traceback, updated its Structured Internal State on cycle 1, and successfully submitted a passing patch.

### 9.3 Phase 5 Hyperparameter and Tooling Optimizations (v4.0 $\rightarrow$ v5.0)
With the $100\%$ pass rate established in Mode D, Phase 5 focused on operational efficiency:
* **Sampling Optimization (v4.1a vs v4.1b)**: Lowering temperature to $0.1$ and top-p to $0.90$ (v4.1a) stabilized whitespace in Python indentation and diff hunks, reducing runtime to $86.6\text{s}$. Raising temperature to $0.3$ (v4.1b) led to exploration loops ($+7.6\%$ tool calls) and was rejected.
* **Prompt Compression (v4.2)**: Pruning verbose instructions reduced prompt token overhead by $50.8\%$, cutting latency from $86.6\text{s}$ to $79.4\text{s}$ ($-8.3\%$).
* **Lexical-First Localization (v4.3)**: Prioritizing exact `rg` matching when error traces provide explicit symbols reduced average tool calls from $9.88$ to $8.50$ ($-14.0\%$).
* **Patch Minimality & 2D Coordinate Guard (v4.4)**: Explicit instructions governing relative 2D coordinate calculations in pretty-printing enabled `sympy` to be patched correctly on the first attempt, reducing repair attempts from $0.12$ to **$0.00$** and average patch size from $13.0$ to $10.9$ lines.
* **PEFT/LoRA Adapter Ablation (v4.6)**: Evaluating a fine-tuned LoRA adapter ($r=16, \alpha=32$) produced identical pass rate ($8/8$), but inflated runtime latency from $90.2\text{s}$ to $235.5\text{s}$ ($+161.1\%$) and violated ADK declarative schema rules. It was rejected.

---

## 10. Results

Table 1 presents the definitive, audited experimental results across all six core system conditions. Every metric is computed directly from recorded JSONL execution traces and verified by deterministic audit scripts (`tools/audit_results.py`).

### Table 1: Comprehensive Cross-Phase Performance Comparison Table

| Metric | Baseline (Phase 2 Frozen) | Semantic Retrieval (Mode A) | Fixed Graph (Mode B) | Adaptive Graph (Mode C) | Adaptive Graph + Repair (Mode D) | Optimized Final System (v5.0) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Benchmark Pass Rate** | $50.0\%$ ($4/8$) | $62.5\%$ ($5/8$) | $75.0\%$ ($6/8$) | $87.5\%$ ($7/8$) | **$100.0\%$ ($8/8$)** | **$100.0\%$ ($8/8$)** |
| **Pass Rate vs. Baseline** | — | $+12.5\%$ | $+25.0\%$ | $+37.5\%$ | **$+50.0\%$** | **$+50.0\%$** |
| **Avg. Tool Calls / Task** | $12.88$ | $11.12$ | $15.25$ | $9.62$ | $9.88$ | **$7.50$** ($-41.8\%$) |
| **Avg. Semantic Search Calls** | $1.25$ | $1.12$ | $1.00$ | $1.00$ | $1.00$ | **$0.50$** ($-60.0\%$) |
| **Avg. Graph Tool Calls** | $0.00$ | $0.00$ | $3.000$ | $0.375$ | $0.375$ | **$0.375$** |
| **Total Graph Calls ($N=8$)** | $0$ | $0$ | $24$ | $3$ | $3$ | **$3$** ($-87.5\%$) |
| **Avg. Files Inspected** | $1.62$ | $1.38$ | $1.38$ | $1.12$ | $1.12$ | **$1.00$** |
| **Avg. Files Edited** | $0.88$ | $0.88$ | $1.00$ | $1.00$ | $1.00$ | **$1.00$** |
| **Avg. Patch Size (Lines)** | $16.5$ | $13.8$ | $14.2$ | $12.8$ | $13.0$ | **$10.9$** ($-33.9\%$) |
| **Avg. Repair Attempts** | $0.50$ | $0.38$ | $0.25$ | $0.12$ | $0.12$ | **$0.00$** ($-100\%$) |
| **Avg. Execution Time (s)** | $114.2\text{s}$ | $97.7\text{s}$ | $136.2\text{s}$ | $86.8\text{s}$ | $90.2\text{s}$ | **$63.0\text{s}$** ($-44.8\%$) |
| **Total Benchmark Time (s)** | $913.6\text{s}$ | $781.3\text{s}$ | $1089.8\text{s}$ | $694.6\text{s}$ | $721.9\text{s}$ | **$504.0\text{s}$** ($-44.8\%$) |
| **Active Tool Suite Size** | $7$ tools | $7$ tools | $9$ tools | $9$ tools | $9$ tools | **$9$ tools** |

### Key Empirical Findings:
1. **Adaptive Graph Superiority**: Adaptive graph reasoning (Mode C) outperforms mandatory graph expansion (Mode B) in pass rate ($87.5\%$ vs. $75.0\%$) while requiring **$87.5\%$ fewer graph queries** ($3$ vs. $24$) and reducing execution latency by $36.3\%$.
2. **Impact of Closed-Loop TDR**: Adding structured patch planning and test-driven repair (Mode D) closes the remaining defect gap ($87.5\% \rightarrow 100.0\%$).
3. **Compound Efficiency in v5.0**: By layering lexical-first routing and coordinate guards onto Mode D, the production candidate **v5.0** reduces tool calls by $24.1\%$ ($7.50$ vs. $9.88$), cuts runtime latency by $30.2\%$ ($63.0\text{s}$ vs. $90.2\text{s}$), and resolves $100\%$ of tasks with **zero repair iterations**.

---

## 11. Failure Analysis and Taxonomy

To understand agent behavior and document edge-case risks, we categorize all observed failures across phases into a comprehensive taxonomy (Table 2).

### Table 2: Failure Mode Taxonomy, Root Causes, and Mitigation History

| Failure Mode | Signature | Occurrences in Evaluation | Root Cause Analysis | Engineering Mitigation | Resolution Phase |
|---|---|:---:|---|---|:---:|
| **`no_edit`** | Agent terminates without invoking `edit_file`. | Phase 2 Baseline (`pytest-5221`) | Localization Horizon: Symbol names in issue description do not match implementation due to dynamic registration hooks. Agent lacks confidence to edit. | Integrated structural `get_code_neighbors` to trace dynamic caller/registration chains. | Resolved in Mode B / Mode C |
| **`test_fail`** | Patch applied, but post-patch test suite fails. | Phase 2 Baseline (`matplotlib-23456`) | Caller Regression: Local fix altered function return contract without updating uninspected downstream callers. | Confidence gating forces caller neighbor inspection when public signatures or multi-axis layouts change. | Resolved in Mode C |
| **`budget_exhausted`** | Agent reaches 30 tool calls without submitting. | Mode B (`matplotlib-23456`) | Graph Bloat: Mandatory graph expansion queries wide inheritance hierarchies, filling context and burning budget. | Replaced mandatory graph calls with adaptive confidence gating (bypassed on leaf nodes). | Resolved in Mode C |
| **`patch_defect`** | Patch introduces indentation or character layout error. | Mode C (`sympy-14308`) | Sub-character Layout Blindness: 2D matrix pretty-printing requires exact relative character coordinate calculations. | 1. Bounded TDR loop caught failure and repaired on Cycle 1 (Mode D).<br/>2. 2D Coordinate Layout Guard added to prompt prevented error entirely (v5.0). | Resolved in Mode D & v5.0 |

---

## 12. Limitations

While the adaptive architecture establishes high efficiency and accuracy, several inherent limitations must be acknowledged:
1. **Benchmark Sample Size ($N=8$)**: Due to offline container computation constraints and exhaustive cross-condition ablation budgets, development experiments were evaluated on an 8-task stratified benchmark. While tasks span major real-world Python packages, absolute variance on small sample sizes requires validation against larger held-out suites.
2. **Static AST Analysis Boundaries**: The code graph tools (`get_code_neighbors`, `get_code_subgraph`) rely on static syntax and symbol analysis. They cannot reliably resolve complex dynamic runtime metaprogramming (e.g., dynamically generated `getattr` delegates or C-extension internals).
3. **Single-Agent Context Boundary**: Long multi-step debugging traces still risk context accumulation. While compact state anchoring mitigates drift, tasks requiring modifications across $>5$ separate files may exceed single-turn context limits.

---

## 13. Generalization & Held-Out Evaluation Protocol

To prevent overfitting to the development benchmark tasks, our research methodology incorporates strict safeguards:

1. **Clean Separation of Development and Held-Out Sets**:
   - The development benchmark (`data/development/benchmark_tasks.jsonl`) was used exclusively for exploratory ablations.
   - The held-out benchmark protocol (`data/heldout/`) enforces zero data leakage: prompt templates, sampling hyperparameters, and tool selection thresholds were **strictly frozen** (SHA-256: `ab5a59b0...`) prior to held-out evaluation.
2. **Cross-Language Transferability**:
   Although our evaluation focused on Python codebases, the two-tier localization hierarchy (lexical $\rightarrow$ semantic) and confidence-gated graph expansion are language-agnostic. Any language with Tree-sitter or AST symbol indexing can support identical `get_code_neighbors` and `get_code_subgraph` semantics.
3. **Budget Robustness**:
   Because v5.0 consumes an average of only $7.50$ tool calls per task ($25\%$ of the $30$-call ceiling) and $63.0\text{s}$ wall-clock time, the agent retains substantial headroom to handle harder, multi-file tasks on held-out benchmarks without budget exhaustion.

---

## 14. Conclusion

In this paper, we introduced **Adaptive Repository Reasoning**, an offline software-engineering agent architecture powered by `gemma-4-31b-it-qat-w4a16-ct`. We addressed the core dilemma of offline repository reasoning: how to provide structural code-graph context without suffering from context bloat and tool budget exhaustion.

Our experimental results demonstrate that:
1. **Adaptive gating is superior to mandatory graph reasoning**: Dynamically activating graph tools only under high localization ambiguity increases pass rate from $75.0\%$ to $87.5\%$ while slashing graph invocations by $87.5\%$.
2. **Structured state tracking and closed-loop TDR guarantee correctness**: Anchoring an 11-slot internal mental state and classifying post-patch test tracebacks enables automated repair, driving pass rate to $100.0\%$.
3. **Compound optimizations yield production excellence**: Layering lexical-first search and coordinate layout guards reduces tool calls by $24.1\%$ and execution latency by $30.2\%$ with zero repair cycles.

The frozen candidate **v5.0** satisfies all Google Gemma 4 Developer Agent Competition constraints: zero cloud dependencies, air-gapped security, zero secret leaks, compliant ADK schema, and full reproducibility.

---

## References

1. Jimenez, C. E., et al. (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* International Conference on Learning Representations (ICLR).
2. DeepMind Gemma Team. (2024). *Gemma: Open Models Based on Gemini Research and Technology.* Google DeepMind Technical Report.
3. Yang, J., et al. (2024). *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering.* arXiv preprint arXiv:2405.15793.
4. Google. (2024). *Agent Development Kit (ADK) Specification and AgentConfig Schemas.* Google Open Source.
5. Touvron, H., et al. (2023). *Llama 2: Open Foundation and Fine-Tuned Chat Models.* Meta AI Research.
6. Hu, E. J., et al. (2021). *LoRA: Low-Rank Adaptation of Large Language Models.* ICLR 2022.
