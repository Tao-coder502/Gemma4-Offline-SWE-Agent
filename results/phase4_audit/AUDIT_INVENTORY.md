# Audit Inventory: Phase 4 Research System

**Date:** October 2026  
**Audit Target:** Phase 4 — Controlled Evaluation, Adaptive Repository Reasoning, Structured Patch Planning & Test-Driven Repair  
**Repository:** `Gemma4-Offline-SWE-Agent`  
**Model:** `gemma-4-31b-it-qat-w4a16-ct`  

---

## 1. System Artifact Inventory

| Artifact | Location | Purpose | Immutable? | Source of Truth? | Used by Report? |
|---|---|---|:---:|:---:|:---:|
| **Sampling Config** | `configs/sampling.yaml` | Declares inference sampling hyperparameters (`temp=0.2`, `top_p=0.95`, `top_k=40`, `max_output_tokens=32768`) | Yes (frozen) | Yes (Inference) | Yes |
| **Phase 2 Baseline Config** | `configs/phase2/agent.yaml` | Phase 2 frozen baseline configuration (strictly 7 tools) | Yes (frozen) | Yes (Phase 2 spec) | Yes |
| **Phase 3 Adaptive Config** | `configs/phase3/agent.yaml` | Phase 3 adaptive graph configuration (9 tools) | Yes (frozen) | Yes (Phase 3 spec) | Yes |
| **Mode A Config** | `configs/phase4/mode_a/agent.yaml` | Mode A Semantic-Only control condition (7 tools) | Yes (frozen) | Yes (Mode A spec) | Yes |
| **Mode B Config** | `configs/phase4/mode_b/agent.yaml` | Mode B Mandatory-Graph condition (9 tools) | Yes (frozen) | Yes (Mode B spec) | Yes |
| **Mode C Config** | `configs/phase4/mode_c/agent.yaml` | Mode C Adaptive-Graph condition (9 tools) | Yes (frozen) | Yes (Mode C spec) | Yes |
| **Mode D Config** | `configs/phase4/mode_d/agent.yaml` | Mode D Adaptive-Graph + Structured State + TDR (9 tools) | Yes (frozen) | Yes (Mode D spec) | Yes |
| **Root Agent Config** | `agent.yaml` | Competition entry point (ADK format, references Mode D) | Yes (active) | Yes (Competition root) | Yes |
| **Phase 2 Prompt** | `prompts/phase2_system.md` | Phase 2 system prompt (7 tools, graph prohibited) | Yes (frozen) | Yes (Phase 2 prompt) | Yes |
| **Phase 3 / Mode C Prompt** | `prompts/system.md` | Adaptive graph reasoning prompt (confidence-gated) | Yes (frozen) | Yes (Mode C prompt) | Yes |
| **Mode A Prompt** | `prompts/system_mode_a.md` | Semantic search only prompt (graph tools prohibited) | Yes (frozen) | Yes (Mode A prompt) | Yes |
| **Mode B Prompt** | `prompts/system_mode_b.md` | Mandatory graph reasoning prompt (unconditional queries) | Yes (frozen) | Yes (Mode B prompt) | Yes |
| **Mode D Prompt** | `prompts/system_mode_d.md` | Structured internal state + 3-cycle test-driven repair prompt | Yes (frozen) | Yes (Mode D prompt) | Yes |
| **Benchmark Dataset** | `data/benchmark_tasks.jsonl` | Standardized 8-task SWE benchmark suite | Yes (frozen) | Yes (Task definitions) | Yes |
| **Sample Tasks** | `data/tasks_sample.jsonl` | 3-task testing subset | Yes | Reference only | No |
| **Benchmark Schema Docs** | `data/README.md` | Arbitrary-N dataset specification & category taxonomy | Yes | Yes (Data standard) | Yes |
| **Raw Mode A Log** | `results/phase4_ablation/mode_a.jsonl` | Raw execution records for Mode A ($N=8$) | **Yes (Immutable)** | **Yes (Raw evidence)** | **Yes** |
| **Raw Mode B Log** | `results/phase4_ablation/mode_b.jsonl` | Raw execution records for Mode B ($N=8$) | **Yes (Immutable)** | **Yes (Raw evidence)** | **Yes** |
| **Raw Mode C Log** | `results/phase4_ablation/mode_c.jsonl` | Raw execution records for Mode C ($N=8$) | **Yes (Immutable)** | **Yes (Raw evidence)** | **Yes** |
| **Raw Mode D Log** | `results/phase4_ablation/mode_d.jsonl` | Raw execution records for Mode D ($N=8$) | **Yes (Immutable)** | **Yes (Raw evidence)** | **Yes** |
| **Raw Archive Backup** | `results/raw/phase4_ablation/` | Read-only preservation copy of raw logs | **Yes (Immutable)** | Yes (Backup evidence) | Reference |
| **Phase 3 Pilot Logs** | `results/phase3_pilot/` | Raw pilot logs for Phase 3 Modes A, B, C ($N=8$) | Yes (frozen) | Historical evidence | Yes |
| **Phase 2 Pilot Log** | `results/phase2_pilot/` | Raw pilot log for Phase 2 baseline ($N=8$) | Yes (frozen) | Historical evidence | Yes |
| **Experiment Logger** | `tools/experiment_logger.py` | JSONL instrumentation and metric schema | Active | Yes (Logging code) | Yes |
| **Task Runner** | `tools/run_baseline.py` | Task execution engine with regex trace extraction | Active | Yes (Execution engine) | Yes |
| **Experiment Orchestrator**| `tools/run_experiment.py` | Top-level runner executing Modes A, B, C, D | Active | Yes (Runner script) | Yes |
| **Result Analyzer** | `tools/analyze_results.py` | Machine evaluation & comparative analysis script | Active | Yes (Audit calculation) | Yes |
| **Metric Definitions** | `docs/metric_definitions.md` | Formal mathematical definitions of evaluation metrics | Yes (frozen) | Yes (Metric standards) | Yes |
| **Phase 4 Report (Prior)** | `docs/phase4_report.md` | Initial Phase 4 synthesis report | Mutable | Synthesis only | Replaced |
| **YAML Validator** | `validate_agent_yaml.py` | Automated ADK schema validator for all configs | Active | Yes (CI/Audit check) | Yes |
| **Prompt Validator** | `validate_system_md.py` | Automated prompt validator for all prompts | Active | Yes (CI/Audit check) | Yes |
| **Submission Packager** | `package_submission.py` | Competition zip archive generator & validator | Active | Yes (Packaging code) | Yes |
| **Submission Archive** | `submission.zip` | Packaged competition archive (Mode D candidate) | Mutable artifact | Derived package | Yes |

---

## 2. Identified Sources of Truth

* **Primary Success / Failure Evidence:** `results/phase4_ablation/mode_{a,b,c,d}.jsonl` (raw task records).
* **Graph Invocations & Tool Traces:** Raw `tool_call_trace` array and `graph_calls` counter in raw JSONL lines.
* **Timing & Duration:** Raw `elapsed_s` float values in JSONL records.
* **Task Definitions & Test Commands:** `data/benchmark_tasks.jsonl`.
* **Metric Aggregation & Statistical Verification:** `tools/analyze_results.py` executed deterministically against raw JSONL logs.
