# Gemma 4 Offline SWE Agent

**Competition:** Google – The Gemma 4 Developer Agent Competition (Kaggle)  
**Phase:** 3 — Adaptive Repository Structure & Code-Graph Reasoning  
**Model:** `gemma-4-31b-it-qat-w4a16-ct` (Offline / Air-Gapped)

---

## Core Research Hypothesis

> **A local SWE agent should not inspect an entire repository indiscriminately.**  
> It should begin with lightweight semantic localization and dynamically request structural context (code-graph neighbors and subgraphs) only when semantic evidence is insufficient or ambiguous.

---

## Project Structure

```
Gemma4-Offline-SWE-Agent/
├── agent.yaml                 # Competition entry point (REQUIRED at root)
├── prompts/
│   └── system.md              # System prompt (Adaptive graph reasoning loop)
├── configs/
│   └── sampling.yaml          # Generation config (temperature, top_p, etc.)
├── adapters/
│   └── README.md              # LoRA adapter placeholder (Phase 4)
├── tools/                     # Local baseline & experiment instrumentation (not in zip)
│   ├── experiment_logger.py   # Multi-mode JSONL experiment logger
│   ├── run_baseline.py        # Benchmark task runner with graph tracking
│   ├── analyze_results.py     # Cross-mode comparative result analyzer
│   └── README.md              # Tools documentation
├── docs/
│   ├── phase2_report.md       # Phase 2 baseline report
│   └── phase3_report.md       # Phase 3 adaptive graph research report
├── data/                      # Local benchmark datasets
│   └── tasks_sample.jsonl     # Sample SWE benchmark tasks
├── results/                   # Comparative experiment result logs
│   ├── phase3_mode_a_semantic.jsonl
│   ├── phase3_mode_b_fixed_graph.jsonl
│   └── phase3_mode_c_adaptive_graph.jsonl
├── package_submission.py      # Submission packaging utility
├── validate_agent_yaml.py     # Phase 3 agent.yaml validation script
├── validate_system_md.py      # Phase 3 prompts/system.md validation script
└── README.md
```

---

## Agent Overview

| Property | Value |
|---|---|
| Model | `gemma-4-31b-it-qat-w4a16-ct` |
| Architecture | Adaptive repository reasoning loop (declarative Google ADK) |
| Tool Registry (9 tools) | `run_command`, `read_file`, `edit_file`, `write_file`, `get_status`, `submit_patch`, `search_similar_code`, `get_code_neighbors`, `get_code_subgraph` |
| Graph Decision Policy | Confidence-gated adaptive expansion (non-mandatory) |
| Sampling Temperature | 0.2 |
| Max Output Tokens | 32,768 |
| External APIs | None (Air-Gapped) |
| Cloud Services | None |

---

## The Adaptive Reasoning Loop

```
Issue received
  │
  ├─► STEP 1: Parse the issue (requested behavior, symptoms, subsystem, terms, expected)
  ├─► STEP 2: Establish repository orientation (ls /workspace, README, tests structure)
  ├─► STEP 3: Semantic localization (search_similar_code + exact rg/grep)
  ├─► STEP 4: Candidate selection & focused reading (read_file with tight line ranges)
  ├─► STEP 5: Confidence & evidence assessment (Adaptive Decision Policy)
  │     ├── IF semantic evidence is sufficient ──────────────┐
  │     └── ELSE (evidence ambiguous / cross-module)         │
  │           │                                              │
  │           ▼                                              │
  ├─► STEP 6: Optional adaptive graph expansion              │
  │           (get_code_neighbors / get_code_subgraph)       │
  │           │                                              │
  │           └──────────────────────┬───────────────────────┘
  │                                  │
  ├─► STEP 7: Form root-cause hypothesis (What / Where / Why / Callers)
  ├─► STEP 8: Evidence verification (run targeted test or write /tmp/repro.py)
  ├─► STEP 9: Produce concise patch plan (minimal change specification)
  ├─► STEP 10: Make minimal patch (edit_file targeted replacement)
  ├─► STEP 11: Run targeted tests (pytest -x -q)
  ├─► STEP 12: Check budget (get_status; abort repair if budget < 15%)
  ├─► STEP 13: Failure diagnosis & triage (patch defect vs pre-existing; max 3 repairs)
  └─► STEP 14: Final validation & submit (submit_patch called exactly once as final action)
```

---

## Empirical Comparison: Modes A vs B vs C

Using the benchmark dataset across identical tasks:

```bash
python tools/analyze_results.py --compare \
    results/phase3_mode_a_semantic.jsonl \
    results/phase3_mode_b_fixed_graph.jsonl \
    results/phase3_mode_c_adaptive_graph.jsonl
```

| Metric | Mode A (Semantic-Only) | Mode B (Fixed-Graph) | Mode C (Adaptive-Graph) |
|---|---|---|---|
| **Success Rate (%)** | 62.5% | 75.0% | **87.5%** |
| **Resolved Tasks** | 5 / 8 | 6 / 8 | **7 / 8** |
| **Avg Tool Calls / Task** | 11.12 | 15.25 | **9.62** |
| **Avg Graph Calls / Task** | 0.00 | 3.00 | **0.38** |
| **Avg Symbols Inspected** | 0.00 | 2.50 | **0.38** |
| **Avg Files Inspected** | 1.38 | 1.38 | **1.12** |
| **Avg Patch Size (lines)** | 13.8 | 14.2 | **12.8** |
| **Avg Repairs / Task** | 0.38 | 0.25 | **0.12** |
| **Avg Elapsed Time (s)** | 97.7s | 136.2s | **86.8s** |

---

## Validation & Packaging

```bash
# 1. Validate Phase 3 agent.yaml
python validate_agent_yaml.py

# 2. Validate Phase 3 prompts/system.md
python validate_system_md.py

# 3. Build & validate submission archive
python package_submission.py
python package_submission.py --validate
```
