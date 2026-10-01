# PiAi — Small Language Models (SLMs) on Edge Hardware

Empirical benchmark suite and runtime architecture to prove and evaluate Small Language Model (0.5B – 3B) performance, reliability, and latency on Raspberry Pi hardware (Pi 4 development baseline, target Pi 5 deployment).

---

## 1. Overview & Core Hypothesis

* **Theory**: While edge single-board computers (SBCs) lack the memory bandwidth to execute large LLMs (7B+), modern **Small Language Models (0.5B–3B)** can achieve real-time, production-viable performance on Raspberry Pis when configured with CPU microarchitecture-tailored runtimes, prompt caching, speculative decoding, and constrained decoding (GBNF/grammar).
* **Target Architectures**:
  * **Development / Baseline**: Raspberry Pi 4 Model B (Quad Cortex-A72 @ 1.5–2.0GHz, 8GB LPDDR4 ~4–5 GB/s bandwidth).
  * **Target / Production**: Raspberry Pi 5 (Quad Cortex-A76 @ 2.4GHz, ARMv8.2-a+dotprod+fp16, 8GB LPDDR4X ~12–15 GB/s bandwidth).

---

## 2. Directory Structure

```
.
├── docs/
│   ├── ARCHITECTURE.md          # Hardware roofline models and compiler optimization details
│   ├── BENCHMARK_SPEC.md        # Workload specifications, test matrix, and evaluation criteria
│   └── superpowers/plans/       # Implementation plans
├── configs/                     # System configs (governor, taskset, llama.cpp flags)
├── grammars/                    # GBNF grammars for JSON schema and tool calling
├── models/                      # GGUF models directory (gitignored)
├── scripts/                     # Benchmark runners, warm-cache evaluators, and setup tools
├── src/                         # Python / Bash inference harness & metrics parsers
└── results/                     # Structured benchmark logs, JSON outputs, and markdown reports
```

---

## 3. Key Optimization Pillars

1. **Microarchitecture Native Compilation**: Vectorized ARM NEON / DotProd math via custom `llama.cpp` builds.
2. **Bandwidth-Aware Quantization**: Leveraging `Q4_0` layout efficiency and `IQ4_XS`/`Q4_K_M` parameter compression.
3. **Speculative Decoding**: Coupling ultra-small draft models (135M–500M) with 1.5B–3B target models.
4. **Constrained Decoding (GBNF)**: Enforcing 100% syntactically valid JSON / tool calling on compact models.
5. **System Prompt Caching**: Eliminating CPU prefill penalties across repeated queries.

---

## 4. Quick Start & Benchmarking

See [docs/BENCHMARK_SPEC.md](docs/BENCHMARK_SPEC.md) for the full execution matrix and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for native runtime setup.

---

## 5. Docker Compose Deployment

The project includes multi-stage containerized deployments with dynamic multi-model routing and built-in WebUI.

### Launch on Raspberry Pi 4 (Dev):
```bash
docker compose --profile pi4 up -d --build
```

### Launch on Raspberry Pi 5 (Prod):
```bash
docker compose --profile pi5 up -d --build
```

### Endpoints:
* **Web UI**: Open `http://<pi-ip>:8080/` in your browser.
* **OpenAI Chat API**: `http://<pi-ip>:8080/v1/chat/completions`
* **Model Catalog**: `http://<pi-ip>:8080/v1/models`
* **Health Check**: `http://<pi-ip>:8080/health`

For configuration flags, GBNF tool calling, and resource tuning, see [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md).
