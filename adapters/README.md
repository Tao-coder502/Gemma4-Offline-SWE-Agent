# Gemma 4 Offline SWE Agent — Adapters Configuration & Status

## Production Status: No LoRA Adapters Active (Frozen v5.0)

In accordance with the frozen Phase 5 production configuration and competition specifications, **no external PEFT/LoRA adapter weights are loaded**.

### Empirical Validation & Rationale (Phase 5 Ablation v4.6)

During the Phase 5 optimization study, a parameter-efficient fine-tuning (PEFT/LoRA) adapter was formally prepared and experimentally evaluated:

* **Adapter Specification**: Low-Rank Adaptation (LoRA), Rank $r = 16$, $\alpha = 32$, target modules `q_proj, v_proj, k_proj, o_proj`.
* **Experimental Condition**: Evaluated on the identical 8-task development benchmark under frozen sampling (`temp=0.1`, `top_p=0.90`).
* **Findings**:
  1. **Pass Rate**: $8 / 8$ ($100.0\%$), identical to the non-LoRA baseline (no accuracy gain).
  2. **Inference Latency**: Average task duration inflated from $90.2\text{s}$ to $235.5\text{s}$ ($+161.1\%$ slowdown), severely degrading runtime efficiency within competition time budgets.
  3. **Schema Compliance**: Google ADK AgentConfig schema strictly disallows non-standard `adapters` or `lora` configuration blocks in `agent.yaml`.
* **Decision**: In strict adherence to Pre-Registered Protocol Rule 7 (*"If performance shows no gain or inflates latency, retain the non-LoRA base model"*), the adapter was **REJECTED**.

The base model `gemma-4-31b-it-qat-w4a16-ct` contains all required capabilities natively when guided by the optimized system instruction pipeline.

### Directory Retention
This directory is preserved in `submission.zip` to document compliance with competition guidelines regarding optional adapter support.

