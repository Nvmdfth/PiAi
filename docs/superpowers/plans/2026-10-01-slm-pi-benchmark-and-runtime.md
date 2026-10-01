# Implementation Plan: SLM Benchmark & Runtime Evaluation on Raspberry Pi

This plan outlines the end-to-end execution to prove and benchmark Small Language Models (0.5B–3B) on Raspberry Pi hardware (Pi 4 baseline `devpi`, ready for Pi 5 transfer).

---

## Proposed File & Directory Layout

```
PiAi/
├── .gitignore
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── BENCHMARK_SPEC.md
│   ├── PI5_MIGRATION_GUIDE.md
│   └── superpowers/plans/
│       └── 2026-10-01-slm-pi-benchmark-and-runtime.md
├── configs/
│   ├── env_pi4.sh
│   └── env_pi5.sh
├── grammars/
│   ├── json.gbnf
│   └── tool_call.gbnf
├── scripts/
│   ├── build_llama_cpp.sh
│   ├── download_models.sh
│   └── run_all_benchmarks.sh
├── src/
│   ├── bench_roofline.py
│   ├── eval_json_tools.py
│   ├── eval_prompt_cache.py
│   ├── eval_speculative.py
│   └── generate_report.py
├── models/                     (gitignored)
└── results/
    ├── raw/                    (gitignored)
    └── BENCHMARK_REPORT.md
```

---

## Phase 1: Environment & Engine Compilation

### Task 1: Native Engine Compilation Script (`scripts/build_llama_cpp.sh`)
* **Objective**: Compile `llama.cpp` optimized specifically for Cortex-A72 (`-mcpu=cortex-a72 -DGGML_NATIVE=ON -DGGML_LTO=ON -DGGML_OPENMP=ON`).
* **Deliverables**:
  * [scripts/build_llama_cpp.sh](file:///home/pi/Projects/PiAi/scripts/build_llama_cpp.sh)
  * Pre-built binaries: `llama-bench`, `llama-cli`, `llama-speculative`, `llama-server`.
* **Verification**: Run `llama-bench --help` and verify CPU feature flags reported during binary startup.

---

## Phase 2: Model Acquisition & Test Grammars

### Task 2: GGUF Model Downloader (`scripts/download_models.sh`)
* **Objective**: Download minimal test matrix GGUFs from Hugging Face hub (SmolLM2-135M/360M, Qwen2.5-0.5B/1.5B/3B, Llama-3.2-1B in Q4_0 / Q4_K_M).
* **Deliverables**:
  * [scripts/download_models.sh](file:///home/pi/Projects/PiAi/scripts/download_models.sh)
* **Verification**: Verify checksums and file sizes in `models/`.

### Task 3: GBNF Grammar Schemas (`grammars/json.gbnf` & `grammars/tool_call.gbnf`)
* **Objective**: Create reusable GBNF grammar files for strict JSON schema output and function calling.
* **Deliverables**:
  * [grammars/json.gbnf](file:///home/pi/Projects/PiAi/grammars/json.gbnf)
  * [grammars/tool_call.gbnf](file:///home/pi/Projects/PiAi/grammars/tool_call.gbnf)
* **Verification**: Validate syntax with `llama-cli --grammar-file`.

---

## Phase 3: Benchmark & Evaluation Suite

### Task 4: Raw Bandwidth & Roofline Benchmarking (`src/bench_roofline.py`)
* **Objective**: Execute `llama-bench` across models, prompt lengths (512, 1024, 2048), generation lengths (128, 256), and thread counts (1..4).
* **Deliverables**:
  * [src/bench_roofline.py](file:///home/pi/Projects/PiAi/src/bench_roofline.py)
* **Verification**: Output raw JSON metrics into `results/raw/roofline_bench.json`.

### Task 5: Headless JSON & Tool-Calling Reliability Harness (`src/eval_json_tools.py`)
* **Objective**: Test 0.5B, 1.5B, and 3B models on 50 synthetic IoT/system log events with and without GBNF grammar to measure parse validity % and accuracy.
* **Deliverables**:
  * [src/eval_json_tools.py](file:///home/pi/Projects/PiAi/src/eval_json_tools.py)
* **Verification**: Verify automated scoring and error categorization.

### Task 6: Prompt Caching & TTFT Evaluator (`src/eval_prompt_cache.py`)
* **Objective**: Measure cold start prompt evaluation vs `--prompt-cache` warm hit on 500-token and 1500-token system contexts.
* **Deliverables**:
  * [src/eval_prompt_cache.py](file:///home/pi/Projects/PiAi/src/eval_prompt_cache.py)
* **Verification**: Confirm latency drop (e.g. 3000ms -> <100ms).

### Task 7: Speculative Decoding Evaluator (`src/eval_speculative.py`)
* **Objective**: Evaluate speedup and acceptance rate of `SmolLM2-135M -> SmolLM2-1.7B` and `Qwen2.5-0.5B -> Qwen2.5-3B`.
* **Deliverables**:
  * [src/eval_speculative.py](file:///home/pi/Projects/PiAi/src/eval_speculative.py)
* **Verification**: Output effective token throughput vs baseline standalone model.

---

## Phase 4: Reporting & Production Migration Guide

### Task 8: Automated Report Generator (`src/generate_report.py`)
* **Objective**: Aggregate all test run outputs into a comprehensive Markdown benchmark report with summary tables and charts.
* **Deliverables**:
  * [src/generate_report.py](file:///home/pi/Projects/PiAi/src/generate_report.py)
  * [results/BENCHMARK_REPORT.md](file:///home/pi/Projects/PiAi/results/BENCHMARK_REPORT.md)

### Task 9: Pi 5 Production Migration Guide (`docs/PI5_MIGRATION_GUIDE.md`)
* **Objective**: Provide step-by-step instructions for transferring models, updating build flags (ARMv8.2-A, KleidiAI), and deployment recommendations.
* **Deliverables**:
  * [docs/PI5_MIGRATION_GUIDE.md](file:///home/pi/Projects/PiAi/docs/PI5_MIGRATION_GUIDE.md)

---

## Phase 5: Verification & Initial Git Commit

* Verify all docs, scripts, and plan structure.
* Commit initial baseline to git repository with structured message.
