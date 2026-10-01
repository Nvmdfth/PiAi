#!/usr/bin/env python3
"""
eval_prompt_cache.py: Evaluates cold vs warm Time To First Token (TTFT)
and prompt processing latency using --prompt-cache.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = ROOT_DIR / "bin"
MODELS_DIR = ROOT_DIR / "models"
CACHE_DIR = ROOT_DIR / "prompt_cache"
RESULTS_DIR = ROOT_DIR / "results" / "raw"

LLAMA_CLI = BIN_DIR / "llama-cli"

SHARED_SYSTEM_PREFIX = """You are an edge intelligence controller for an industrial IoT plant.
Your role is to monitor hundreds of temperature, pressure, vibration, and flow sensors across 12 zones.
Zone 1: Primary coolant loop. Normal operating pressure 120-140 PSI, temperature 45-65C.
Zone 2: Secondary heat exchanger. Normal operating pressure 90-110 PSI, temperature 70-85C.
Zone 3: Turbogenerator stator. Normal vibration RMS < 2.5 mm/s, temperature < 95C.
Zone 4: Substation transformer. Max oil temperature 80C, ambient delta < 35C.
Zone 5: Water filtration intake. Flow rate 400-500 gpm, particulate index < 15.
Zone 6: Air compressor bank. Discharge pressure 150 PSI, cycle frequency 4/hr.
Zone 7: Fuel storage depot. Inert gas blanket pressure 1.2 bar, leak detection zero-tolerance.
Zone 8: Emergency exhaust dampers. Actuator test weekly, response latency < 500ms.
Zone 9: Wastewater effluent treatment. pH 6.8-7.4, turbidity < 5 NTU.
Zone 10: Chemical dosing feeder. Flow rate 2.5 L/hr, hopper level > 20%.
Zone 11: Main conveyor belt drive. Motor current draw 45-55A, bearing temp < 60C.
Zone 12: Environmental emissions stack. CO2 < 450 ppm, NOx < 15 ppm, SO2 < 5 ppm.
Whenever anomalous readings are observed, recommend immediate action."""

QUERY_COLD = "Alert: Zone 1 pressure is 165 PSI. Recommend action."
QUERY_WARM = "Alert: Zone 3 vibration RMS reached 4.1 mm/s. Recommend action."

def check_binary():
    if not LLAMA_CLI.is_file():
        print(f"Error: llama-cli binary not found at {LLAMA_CLI}.", file=sys.stderr)
        sys.exit(1)

def parse_llama_timings(stderr_text):
    prompt_ms = 0.0
    eval_ms = 0.0
    
    # prompt eval time = 1234.56 ms / 250 tokens
    m_prompt = re.search(r"prompt eval time\s*=\s*([\d\.]+)\s*ms", stderr_text)
    if m_prompt:
        prompt_ms = float(m_prompt.group(1))
        
    # eval time = 567.89 ms / 64 runs
    m_eval = re.search(r"eval time\s*=\s*([\d\.]+)\s*ms", stderr_text)
    if m_eval:
        eval_ms = float(m_eval.group(1))
        
    return prompt_ms, eval_ms

def run_cache_benchmark(model_path, threads=3):
    check_binary()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    model_file = Path(model_path)
    cache_file = CACHE_DIR / f"{model_file.stem}_cache.bin"
    
    if cache_file.exists():
        cache_file.unlink()

    prompt_cold = f"<|im_start|>system\n{SHARED_SYSTEM_PREFIX}<|im_end|>\n<|im_start|>user\n{QUERY_COLD}<|im_end|>\n<|im_start|>assistant\n"
    prompt_warm = f"<|im_start|>system\n{SHARED_SYSTEM_PREFIX}<|im_end|>\n<|im_start|>user\n{QUERY_WARM}<|im_end|>\n<|im_start|>assistant\n"

    print(f"\n[EVAL] Testing prompt cache on {model_file.stem}...")

    # Run 1: Cold start (populate cache)
    cmd_cold = [
        str(LLAMA_CLI),
        "-m", str(model_file),
        "-p", prompt_cold,
        "--prompt-cache", str(cache_file),
        "--prompt-cache-all",
        "-n", "32",
        "-t", str(threads),
        "--no-display-prompt",
        "--no-conversation"
    ]
    
    start_cold = time.time()
    res_cold = subprocess.run(cmd_cold, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    lat_cold = time.time() - start_cold
    cold_prompt_ms, _ = parse_llama_timings(res_cold.stderr)

    # Run 2: Warm start (re-use cache with different user query)
    cmd_warm = [
        str(LLAMA_CLI),
        "-m", str(model_file),
        "-p", prompt_warm,
        "--prompt-cache", str(cache_file),
        "-n", "32",
        "-t", str(threads),
        "--no-display-prompt",
        "--no-conversation"
    ]

    start_warm = time.time()
    res_warm = subprocess.run(cmd_warm, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    lat_warm = time.time() - start_warm
    warm_prompt_ms, _ = parse_llama_timings(res_warm.stderr)

    speedup = round(lat_cold / lat_warm, 2) if lat_warm > 0 else 1.0

    print(f"  Cold Wall: {lat_cold:.2f}s (Prompt: {cold_prompt_ms:.1f}ms) | Warm Wall: {lat_warm:.2f}s (Prompt: {warm_prompt_ms:.1f}ms) | Speedup: {speedup}x")

    return {
        "model": model_file.name,
        "returncode_cold": res_cold.returncode,
        "returncode_warm": res_warm.returncode,
        "cold_wall_latency_s": round(lat_cold, 3),
        "warm_wall_latency_s": round(lat_warm, 3),
        "cold_prompt_eval_ms": cold_prompt_ms,
        "warm_prompt_eval_ms": warm_prompt_ms,
        "speedup_factor": speedup,
        "cache_size_bytes": cache_file.stat().st_size if cache_file.exists() else 0
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate prompt caching performance.")
    parser.add_argument("--models", nargs="*", help="Model paths to evaluate")
    parser.add_argument("--threads", type=int, default=3)
    args = parser.parse_args()

    if not args.models:
        model_paths = list(MODELS_DIR.glob("*.gguf"))
    else:
        model_paths = [Path(m) for m in args.models]

    if not model_paths:
        print(f"No models found. Run scripts/download_models.sh first.", file=sys.stderr)
        sys.exit(1)

    results = []
    for m in model_paths:
        res = run_cache_benchmark(m, threads=args.threads)
        results.append(res)

    out_file = RESULTS_DIR / "eval_prompt_cache.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved prompt cache evaluation results to {out_file}")

if __name__ == "__main__":
    main()
