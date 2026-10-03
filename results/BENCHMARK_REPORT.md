# Small Language Model (SLM) Benchmark Report

*Generated on: 2026-10-02 22:00:24*

## 1. Executive Summary
- Empirical benchmarks collected across native ARM NEON inference on Cortex-A72.
- Structured GBNF constrained decoding evaluated against raw unconstrained sampling.
- System prompt caching evaluated for TTFT amortization across repeated queries.
- Speculative drafting evaluated for bandwidth amortization on small parameter models.


## 2. Raw Generation & Prompt Processing (Roofline)
| Model | Threads | Test Type | Speed (tokens/sec) | Latency (ms/token) |
| :--- | :---: | :---: | :---: | :---: |
| `qwen2.5-0.5b-q4_0.gguf` | 3 | Prompt (512t) | **15.81** | 63.25 |
| `qwen2.5-0.5b-q4_0.gguf` | 3 | Gen (128t) | **8.03** | 124.53 |
| `qwen2.5-0.5b-q4_0.gguf` | 4 | Prompt (512t) | **15.75** | 63.49 |
| `qwen2.5-0.5b-q4_0.gguf` | 4 | Gen (128t) | **7.58** | 131.93 |
| `smollm2-135m-q4_0.gguf` | 3 | Prompt (512t) | **40.66** | 24.59 |
| `smollm2-135m-q4_0.gguf` | 3 | Gen (128t) | **17.42** | 57.41 |
| `smollm2-135m-q4_0.gguf` | 4 | Prompt (512t) | **45.19** | 22.13 |
| `smollm2-135m-q4_0.gguf` | 4 | Gen (128t) | **25.04** | 39.94 |
| `qwen2.5-1.5b-q4_0.gguf` | 3 | Prompt (512t) | **4.07** | 245.7 |
| `qwen2.5-1.5b-q4_0.gguf` | 3 | Gen (128t) | **2.62** | 381.68 |
| `qwen2.5-1.5b-q4_0.gguf` | 4 | Prompt (512t) | **4.2** | 238.1 |
| `qwen2.5-1.5b-q4_0.gguf` | 4 | Gen (128t) | **2.64** | 378.79 |


## 3. Headless JSON & Tool-Calling Reliability
| Model | Unconstrained Valid % | Grammar Valid % | Action Match % | Avg Latency (s) |
| :--- | :---: | :---: | :---: | :---: |
| `qwen2.5-0.5b-q4_0.gguf` | 100.0% | **100.0%** | 60.0% | 19.284s |
| `smollm2-135m-q4_0.gguf` | 0.0% | **80.0%** | 40.0% | 10.156s |
| `qwen2.5-1.5b-q4_0.gguf` | 100.0% | **100.0%** | 80.0% | 63.311s |


## 4. Prompt Caching & TTFT Acceleration
| Model | Cold Latency (s) | Warm Latency (s) | Cold Prompt (ms) | Warm Prompt (ms) | Speedup Factor |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `qwen2.5-1.5b-q4_0` | 76.21s | **13.476s** | 66534.2 | 3514.1 | **5.66x** |
| `qwen2.5-coder-1.5b-q4_0` | 100.908s | **15.247s** | 89334.4 | 4418.4 | **6.62x** |


## 5. Speculative Decoding Multiplier
| Target Model | Draft Model | Baseline (tok/s) | Speculative (tok/s) | Speedup |
| :--- | :--- | :---: | :---: | :---: |
| `qwen2.5-1.5b-q4_0.gguf` | `qwen2.5-0.5b-q4_0.gguf` | 0.96 | **1.37** | **1.43x** |
