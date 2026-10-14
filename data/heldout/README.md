# Held-Out Evaluation Dataset Repository

**Status:** `NOT_READY / NOT_YET_EXECUTED`  
**Target Sample Size:** $N = 64\text{ to }100$ tasks  
**Stratification:** 8 Canonical Structural Categories (8 to 12 tasks per category)  
**Schema Definition:** [`task_manifest_schema.json`](file:///c:/Users/DELL/Downloads/Gemma4-Offline-SWE-Agent/data/heldout/task_manifest_schema.json)  

---

## Non-Negotiable Governance Principles

1. **NO TASK FABRICATION**:
   In strict accordance with Absolute Rule 1, benchmark tasks must originate from genuine real-world SWE-bench repositories. No mock tasks or synthetic instances are fabricated.
2. **STRICT ISOLATION**:
   Held-out tasks must NEVER be read or accessed by optimization scripts (`tools/run_optimization_study.py`, prompt tuning, or hyperparameter exploration).
3. **PRE-REGISTRATION**:
   Prior to running the held-out evaluation on the frozen v5.0 production candidate, the manifest `data/heldout/task_manifest.json` will be generated, validated via `tools/verify_task_manifest.py`, and signed with an immutable SHA-256 hash.
4. **EXECUTION STATUS**:
   This evaluation has NOT yet been executed. Generalization claims remain strictly **UNTESTED** until the frozen evaluation is carried out.
