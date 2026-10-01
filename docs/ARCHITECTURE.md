# System Architecture & Roofline Model

## 1. Physical Hardware & Memory Roofline

On CPU-based LLM inference, the generation/decode phase is primarily **memory-bandwidth bound**:
$$\text{Max Throughput (tokens/s)} \approx \frac{\text{Usable RAM Bandwidth (GB/s)}}{\text{Model Size in RAM (GB)}}$$

| Metric / Parameter | Raspberry Pi 4 Model B | Raspberry Pi 5 |
| :--- | :--- | :--- |
| **CPU Architecture** | 4× Cortex-A72 (ARMv8.0-A) | 4× Cortex-A76 (ARMv8.2-A) |
| **Clock Speed** | 1.50 GHz (overclockable to 2.0 GHz) | 2.40 GHz |
| **Vector ISA Support** | ARM NEON (`asimd`, `fp`) | ARM NEON, DotProd (`dotprod`), FP16 (`fp16`) |
| **RAM Type & Bus** | 8GB LPDDR4-3200 (32-bit single/dual bus) | 8GB LPDDR4X-4267 (dual 32-bit channels) |
| **Measured Memory Bandwidth**| ~4.0 – 5.2 GB/s | ~12.0 – 15.5 GB/s |
| **Estimated 0.5B (Q4 ~0.35GB)**| **~10 – 14 tok/s** | **~30 – 42 tok/s** |
| **Estimated 1.5B (Q4 ~0.90GB)**| **~4.0 – 5.5 tok/s** | **~12 – 16 tok/s** |
| **Estimated 3B (Q4 ~1.90GB)** | **~1.8 – 2.5 tok/s** | **~6 – 8 tok/s** |

---

## 2. Compilation Flags & Engine Configurations

### Pi 4 (`devpi` / Cortex-A72)
* Flags: `-mcpu=cortex-a72 -DGGML_NATIVE=ON -DGGML_LTO=ON -DGGML_OPENMP=ON`
* Quantizer tuning: `Q4_0` utilizes runtime interleaved repacking (`GGML_CPU_AARCH64`), optimizing NEON register load pipelines.

### Pi 5 (Cortex-A76)
* Flags: `-mcpu=cortex-a76 -march=armv8.2-a+dotprod+fp16 -DGGML_NATIVE=ON -DGGML_LTO=ON`
* KleidiAI acceleration for quantized int8 dot product arithmetic.

---

## 3. Runtime Optimizations

1. **Thread Discipline**:
   * Prefill (compute bound): 4 threads (`-t 4`).
   * Decode (bandwidth bound): 3 threads (`-t 3`) via `taskset` to eliminate core contention with OS services.
2. **Memory Locking (`--mlock`)**:
   * Ensures model weights remain pinned in physical RAM, avoiding page-cache thrashing.
3. **Prompt Cache Reuse**:
   * Pre-evaluates system prompts and static tool definitions into `--prompt-cache` binary files, reducing TTFT from seconds to milliseconds.
4. **Constrained GBNF Decoding**:
   * Grammars enforce valid JSON grammar on token generation, eliminating parse failures on smaller parameter models.
