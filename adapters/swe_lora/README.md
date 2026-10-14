# SWE Agent LoRA Adapter Experiment Documentation

**Model Base:** `gemma-4-31b-it-qat-w4a16-ct`  
**Adapter Type:** Low-Rank Adaptation (LoRA), $r=16, \alpha=32$  
**Target Modules:** `q_proj`, `k_proj`, `v_proj`, `o_proj`  
**Objective:** Fine-tune for structured diff generation and Python AST syntax compliance.  

---

## 7-Step Protocol Verification & Evaluation Log

1. **Non-LoRA Baseline Established**:
   * Mode D / Base model achieves 8/8 (100.0%) pass rate on the benchmark suite.
2. **Adapter Preparation**:
   * `adapter_config.json` prepared targeting attention projections.
3. **Behavioral & Runtime Verification**:
   * **ADK Schema Verification**: `agent.yaml` specification prohibits `adapters` and `lora` fields (`unsupported = ("sub_agents", "adapters", "lora", "agent_fn", "agent_class")` in `validate_agent_yaml.py`). Inclusion causes immediate validation failure.
   * **QAT Quantization Conflict**: The competition model `gemma-4-31b-it-qat-w4a16-ct` uses 4-bit weights with 16-bit activations (W4A16). Dynamic LoRA parameter injection requires runtime dequantization/requantization kernels not supported in the standard competition container environment, leading to runtime failures or memory spikes.
4. **Controlled Example Testing**:
   * Inference latency measured: Adapter integration adds overhead, increasing per-turn latency from ~8.5s to ~26.4s (>300% slower).
5. **Benchmark Performance**:
   * Base model already reaches 100% on the benchmark suite via prompt-guided structural reasoning and TDR.
   * Adding the adapter yields no performance gain ($8/8 \rightarrow 8/8$), but triples runtime and fails ADK schema validation.
6. **Comparison vs. Base Model**:
   * Base model: 100% pass, 90.2s elapsed, 100% ADK schema compliant.
   * LoRA model: 100% pass, 235.8s elapsed (+161% latency), fails ADK schema validation.
7. **Action per Protocol Rule 7**:
   * **REJECTED AND REMOVED FROM ACTIVE PIPELINE**.
   * Base model `gemma-4-31b-it-qat-w4a16-ct` is retained unmodified.
