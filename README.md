# Gemma 4 Offline SWE Agent

**Competition:** Google – The Gemma 4 Developer Agent Competition (Kaggle)  
**Phase:** 4 — Controlled Evaluation, Structured Patch Planning & Test-Driven Repair  
**Model:** `gemma-4-31b-it-qat-w4a16-ct` (Offline / Air-Gapped)  
**Status:** Completed, Audited & Packaged  

---

## Core Research Hypothesis

> **A local SWE agent should not inspect an entire repository indiscriminately.**  
> It should begin with lightweight semantic localization and dynamically request structural context (code-graph neighbors and subgraphs) only when semantic evidence is insufficient or ambiguous. When paired with structured patch planning and test-driven repair, it achieves superior patch reliability with minimal exploration overhead.

---

## Project Structure

```text
Gemma4-Offline-SWE-Agent/
├── agent.yaml                 # Competition entry point (defaults to Phase 4 / Mode D)
├── prompts/
│   ├── phase2_system.md       # Phase 2 frozen baseline prompt (7 tools)
│   ├── system.md              # Phase 3 adaptive prompt / Mode C (9 tools)
│   ├── system_mode_a.md       # Phase 4 Mode A prompt (semantic-only control)
│   ├── system_mode_b.md       # Phase 4 Mode B prompt (mandatory graph)
│   └── system_mode_d.md       # Phase 4 Mode D prompt (structured state + TDR)
├── configs/
│   ├── sampling.yaml          # Generation config (temp=0.2, top_p=0.95, etc.)
│   ├── phase2/agent.yaml      # Phase 2 frozen baseline configuration
│   ├── phase3/agent.yaml      # Phase 3 adaptive graph configuration
│   └── phase4/                # Phase 4 ablation study configurations
│       ├── mode_a/agent.yaml  # Mode A (Semantic retrieval only)
│       ├── mode_b/agent.yaml  # Mode B (Mandatory graph reasoning)
│       ├── mode_c/agent.yaml  # Mode C (Adaptive graph reasoning)
│       └── mode_d/agent.yaml  # Mode D (Adaptive graph + Structured State + TDR)
├── adapters/
│   └── README.md              # LoRA adapter placeholder (Phase 5)
├── tools/                     # Local experiment instrumentation (not in zip)
│   ├── experiment_logger.py   # JSONL experiment logger with Mode D TDR fields
│   ├── run_baseline.py        # Task runner with graph & TDR signal tracking
│   ├── run_experiment.py      # Top-level orchestrator: runs all 4 modes
│   ├── analyze_results.py     # Comparative analyzer with transition audit
│   └── README.md              # Tools documentation
├── docs/
│   ├── metric_definitions.md  # Formal metric standards
│   ├── phase2_report.md       # Phase 2 audit report
│   ├── phase3_report.md       # Phase 3 graph reasoning report
│   ├── research_audit_report.md# Formal audit report of Phases 2 & 3
│   └── phase4_report.md       # Phase 4 complete research report & paper draft
├── data/                      # Standardized benchmark datasets
│   ├── README.md              # Dataset schema & arbitrary-N specifications
│   ├── tasks_sample.jsonl     # Sample tasks
│   └── benchmark_tasks.jsonl  # Standardized 8-task benchmark suite
├── results/                   # Raw empirical experiment result logs
│   ├── phase2_pilot/          # Phase 2 frozen baseline pilot
│   ├── phase3_pilot/          # Phase 3 pilot results (A, B, C)
│   └── phase4_ablation/       # Phase 4 ablation study results (A, B, C, D)
│       ├── mode_a.jsonl
│       ├── mode_b.jsonl
│       ├── mode_c.jsonl
│       └── mode_d.jsonl
├── package_submission.py      # Competition zip packager (Phase 2, 3, or 4)
├── validate_agent_yaml.py     # Multi-phase agent.yaml validator (Phases 2, 3, 4)
├── validate_system_md.py      # Multi-phase prompts/system.md validator
└── README.md
```

---

## Controlled Evaluation: 4-Way Ablation Study

Evaluated across the standardized benchmark suite of real-world Python repositories (Requests, Flask, Matplotlib, Scikit-learn, SymPy, Django, Pytest, Sphinx):

```bash
# Run all four modes and generate the comparative analysis:
python tools/run_experiment.py --tasks data/benchmark_tasks.jsonl --outdir results/phase4_ablation
```

### Ablation Results Summary

| Metric | Mode A (Semantic-Only) | Mode B (Mandatory-Graph) | Mode C (Adaptive-Graph) | Mode D (Full Capability) |
|---|:---:|:---:|:---:|:---:|
| **Patch Success Rate (%)** | 62.5% | 75.0% | 87.5% | **100.0%** |
| **Resolved Tasks** | 5 / 8 | 6 / 8 | 7 / 8 | **8 / 8** |
| **Avg Tool Calls / Task** | 11.12 | 15.25 | 9.62 | **9.88** |
| **Avg Graph Calls / Task** | 0.00 | 3.00 | 0.38 | **0.38** |
| **Total Graph Calls** | 0 | 24 | 3 | **3** |
| **Avg Patch Size (lines)** | 13.8 | 14.2 | 12.8 | **13.0** |
| **Avg Repairs / Task** | 0.38 | 0.25 | 0.12 | **0.12** |
| **Tasks w/ Patch Plan** | 0% | 0% | 0% | **100%** |
| **Avg Elapsed Time (s)** | 97.7s | 136.2s | 86.8s | **90.2s** |

---

## Structured Internal Reasoning State (Mode D)

Mode D introduces a lightweight, verifiable internal state block updated progressively at each stage without exposing unconstrained chain-of-thought tokens:

```text
INTERNAL STATE
--------------
Issue          : <one-sentence summary of what is broken>
Error Symptoms : <exact error message or failing assertion>
Subsystem      : <top-level package / module implicated>
Candidate File : <path/to/file.py>
Candidate Fn   : <function_or_method_name>
Graph Used     : <yes/no — and which tool if yes>
Hypothesis     : <one-sentence root cause: what/where/why>
Confidence     : <high | medium | low>
Patch Plan     : <precise description of the edit: file, line range, change>
Test Command   : <exact pytest command to validate the fix>
Test Outcome   : <pass | fail | unknown>
Repair Cycle   : <0 | 1 | 2 | 3>
Repair Decision: <continue | halt>
```

---

## Validation & Packaging

```bash
# 1. Validate all agent configurations (Phase 2, 3, 4)
python validate_agent_yaml.py

# 2. Validate all system prompts (Phase 2, 3, 4)
python validate_system_md.py

# 3. Build & validate official competition package (Mode D candidate)
python package_submission.py --phase 4
python package_submission.py --validate
```
