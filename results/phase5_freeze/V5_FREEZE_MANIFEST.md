# Version 5.0 Production Candidate Freeze Manifest

**Repository:** `Gemma4-Offline-SWE-Agent`  
**Status:** `FROZEN_DEVELOPMENT_CANDIDATE`  
**Freeze Timestamp:** `2026-10-01T03:15:00Z`  
**Git Commit:** `a5736c980278e60b3c5a8e2712cf28e68df56213`  

---

## 1. Frozen Artifact Hashes

| Component | Path | SHA-256 Checksum |
|---|---|---|
| **System Prompt** | [`prompts/system_v5_optimized.md`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/prompts/system_v5_optimized.md) | `ab5a59b02e830772b9967012e9051a6c7c83442ed83612b39e0b36ff3621bca6` |
| **Sampling Config** | [`configs/phase5/v5_0_final/sampling.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase5/v5_0_final/sampling.yaml) | `298ba75a74286937994430731d4d1b0267eabecfbcde16e06ad5408414269e6d` |
| **Agent YAML (Phase 5)** | [`configs/phase5/v5_0_final/agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/configs/phase5/v5_0_final/agent.yaml) | `c994bda2f443f6cb719b20793b2f26e62117bf4ff0a6d8408f036d774a4b28f1` |
| **Root Agent YAML** | [`agent.yaml`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/agent.yaml) | `788c258479db550da65767d26e12484c18bb36611d110c731596bdfd6043095b` |
| **Tool Registry (9 tools)** | Sorted tool set JSON | `c2a708a27cae2b8095f4bfc79115ad5748a727a603c725a7d476210418517ef8` |
| **Development Benchmark** | [`data/development/benchmark_tasks.jsonl`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/data/development/benchmark_tasks.jsonl) | `92ca377234e597ae8ba22aa23d939ca9c2c5c540b595830a674117a8357b487e` |

---

## 2. Frozen Configuration Specifications

* **Model**: `gemma-4-31b-it-qat-w4a16-ct` (Offline / Air-Gapped)
* **Sampling Parameters**:
  - `temperature = 0.1`
  - `top_p = 0.90`
  - `max_output_tokens = 32768`
* **Official 9-Tool Suite**:
  - `run_command`
  - `read_file`
  - `edit_file`
  - `write_file`
  - `get_status`
  - `submit_patch`
  - `search_similar_code`
  - `get_code_neighbors`
  - `get_code_subgraph`
* **Architectural Decisions**:
  - Two-tier localization: Lexical ripgrep (`rg`) tier before semantic search fallback.
  - Confidence-gated adaptive structural graph queries (bypassed on local leaf bugs).
  - 11-slot Structured Internal State anchor.
  - Patch minimality with 2D relative coordinate layout calculation guard.
  - Targeted pytest execution (`-k` filters) before and after edits.
  - Bounded closed-loop test-driven repair (max 3 cycles) with traceback failure classification.
  - Explicit early stopping once test validation passes and clean diff is verified.

---

## 3. Strict Research Freeze Contract

1. **NO CODE MODIFICATIONS**: Do not edit `prompts/system_v5_optimized.md`, `configs/phase5/v5_0_final/`, or root `agent.yaml`.
2. **NO HYPERPARAMETER TUNING**: Do not alter temperature, top_p, token budgets, or tool timeouts.
3. **ISOLATION FROM HELD-OUT DATA**: The frozen candidate must NOT be adapted, fine-tuned, or re-prompted against any held-out benchmark tasks.
4. **BENCHMARK CLASSIFICATION**: All existing Phase 5 results on `data/development/benchmark_tasks.jsonl` are strictly classified as **development / optimization findings**. Generalization remains **UNTESTED** until the held-out evaluation is formally executed.
