# Raspberry Pi 5 Production Migration Guide

This guide details the steps to transition models, builds, and runtime settings from the Raspberry Pi 4 development baseline to a production Raspberry Pi 5 environment.

---

## 1. Hardware & Performance Expectations

| Dimension | Raspberry Pi 4 (Dev) | Raspberry Pi 5 (Prod) | Expected Delta |
| :--- | :--- | :--- | :--- |
| **CPU Core** | Cortex-A72 @ 1.5–2.0 GHz | Cortex-A76 @ 2.4 GHz | ~2.2× single-core IPC |
| **ISA / SIMD** | ARMv8.0 NEON | ARMv8.2-A + DotProd + FP16 | ~3× dot product speedup |
| **RAM Bandwidth** | ~4.5 GB/s (LPDDR4) | ~14.5 GB/s (LPDDR4X) | ~3.0× token generation bandwidth |
| **0.5B Model Decode**| ~10–14 tok/s | **~35–45 tok/s** | Ultra-responsive |
| **1.5B Model Decode**| ~4.0–5.5 tok/s | **~13–18 tok/s** | Fast interactive conversational |
| **3B Model Decode**  | ~1.8–2.5 tok/s | **~6.5–9.0 tok/s** | Production interactive |

---

## 2. Compilation on Pi 5

Execute the compilation using the Pi 5 configuration profile:

```bash
# Source environment variables and compile
./scripts/build_llama_cpp.sh pi5
```

This activates:
* `-mcpu=cortex-a76 -march=armv8.2-a+dotprod+fp16`
* `-DGGML_CPU_KLEIDIAI=ON` (Arm KleidiAI accelerated micro-kernels)
* `-DGGML_OPENMP=ON -DGGML_LTO=ON`

---

## 3. Production Deployment Recommendations

1. **System Governor & Cooling**:
   * Ensure active fan cooling (Raspberry Pi Active Cooler) to avoid thermal throttling above 80°C.
   * Lock CPU scaling to performance:
     ```bash
     sudo cpufreq-set -g performance
     ```
2. **Server Daemon Mode**:
   * Deploy `llama-server` behind a reverse proxy (e.g. Nginx or Traefik):
     ```bash
     ./bin/llama-server \
         -m models/qwen2.5-1.5b-q4_0.gguf \
         --host 0.0.0.0 --port 8080 \
         -t 3 -c 4096 \
         --mlock --slot-save-path slot_cache
     ```
3. **Draft Speculative Pairings (For 3B+ Models)**:
   * Target: `Qwen2.5-3B-Instruct-Q4_0.gguf`
   * Draft: `Qwen2.5-0.5B-Instruct-Q4_0.gguf`
   * Achieves ~10–12 tok/s on Pi 5.
