# Main LoRA Adapter for Gemma 4 (31B QAT W4A16 CT)

This directory contains the parameter-efficient fine-tuning (PEFT) LoRA adapter
tailored for autonomous software engineering on SWE-bench tasks.

## Adapter Architecture
- **Base Model**: `google/gemma-4-31b-it-qat-w4a16-ct`
- **PEFT Type**: LoRA (Low-Rank Adaptation)
- **Rank ($r$)**: 16
- **Alpha ($\alpha$)**: 32
- **Dropout**: 0.05
- **Target Attention Projections**: `q_proj`, `k_proj`, `v_proj`, `o_proj`
- **Serialization Format**: Hugging Face `.safetensors`

## Objective
The adapter is optimized to:
1. Predict minimal, surgical unified git diffs from problem statements and failing test outputs.
2. Structure tool calls without syntax errors or hallucinated parameters.
3. Suppress extraneous edits (docstrings, refactoring, whitespace shifts).

## Files
- `adapter_config.json`: PEFT configuration schema.
- `adapter_model.safetensors`: Safetensors binary adapter weights.
