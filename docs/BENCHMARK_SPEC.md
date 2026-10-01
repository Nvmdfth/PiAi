# Benchmark Specification & Test Matrix

## 1. Objectives

Empirically evaluate and document the operational boundaries of running Small Language Models on Raspberry Pi hardware across both **Interactive Conversational** and **Headless Agent / Structured JSON** workloads.

---

## 2. Evaluation Workloads

### Workload A: Headless JSON Extraction & Tool Dispatch
* **Task**: Parse unstructured telemetry/user logs into strictly conforming JSON function calls (e.g. IoT device control, alert severity classification).
* **Key Metrics**:
  * Tool-call schema validity rate (%) with and without GBNF grammar constraints.
  * Cold vs Warm TTFT (Time To First Token).
  * Generation throughput (tokens/sec).

### Workload B: Interactive Conversational Q&A
* **Task**: Multi-turn dialogue, summarizing 500–1000 token context, and interactive command execution.
* **Key Metrics**:
  * Sustained decode speed (tokens/sec vs human reading baseline of ~4–5 tps).
  * Cold vs Warm prompt evaluation latency.
  * Memory footprint (RSS MB).

---

## 3. Model Evaluation Matrix

| Model Tier | Model Name | Parameter Size | Primary Quantizations | Intended Role |
| :--- | :--- | :--- | :--- | :--- |
| **Draft / Floor** | `SmolLM2-135M-Instruct` | 135M | `Q4_0`, `Q8_0` | Speculative drafting, fast text classification |
| **Draft / Micro** | `SmolLM2-360M-Instruct` | 360M | `Q4_0`, `Q8_0` | Speculative drafting, compact intent parsing |
| **Sub-1B Tier** | `Qwen2.5-0.5B-Instruct` | 490M | `Q4_0`, `Q4_K_M`, `Q8_0` | Fast tool router, low-latency JSON extractor |
| **1B–1.5B Tier** | `Llama-3.2-1B-Instruct` | 1.2B | `Q4_0`, `Q4_K_M` | Balanced interactive chat & assistant |
| **1B–1.5B Tier** | `Qwen2.5-1.5B-Instruct` | 1.54B | `Q4_0`, `Q4_K_M` | High-accuracy structured reasoning & coding |
| **3B Tier (Ceiling)**| `Qwen2.5-3B-Instruct` | 3.09B | `Q4_0`, `IQ3_M` | Complex multi-step reasoning (Pi 4 limit / Pi 5 target) |

---

## 4. Test Runs & Ablations

1. **Ablation 1: Compiler & Vector Optimization**
   * Generic build vs `-mcpu=cortex-a72 -DGGML_NATIVE=ON`.
2. **Ablation 2: Quantization Efficiency**
   * Compare `Q4_0` (interleaved NEON) vs `Q4_K_M` vs `Q8_0`.
3. **Ablation 3: Speculative Decoding Speedup**
   * `SmolLM2-135M` $\rightarrow$ `SmolLM2-1.7B`
   * `Qwen2.5-0.5B` $\rightarrow$ `Qwen2.5-3B`
4. **Ablation 4: Prompt Cache Acceleration**
   * Measure TTFT cold start vs preloaded `--prompt-cache`.
5. **Ablation 5: Grammars vs Raw Sampling**
   * Measure JSON schema error rate under raw sampling vs GBNF grammar.
