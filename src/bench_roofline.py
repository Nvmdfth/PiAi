#!/usr/bin/env python3
"""
bench_roofline.py: Measures raw prompt evaluation (pp) and token generation (tg)
bandwidth across thread counts and model formats using llama-bench.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = ROOT_DIR / "bin"
MODELS_DIR = ROOT_DIR / "models"
RESULTS_DIR = ROOT_DIR / "results" / "raw"

LLAMA_BENCH = BIN_DIR / "llama-bench"

def check_binary():
    if not LLAMA_BENCH.is_file():
        print(f"Error: llama-bench binary not found at {LLAMA_BENCH}. Run scripts/build_llama_cpp.sh first.", file=sys.stderr)
        sys.exit(1)

def run_roofline(models, threads=[1, 2, 3, 4], p_lens=[512], n_gens=[128], reps=3):
    check_binary()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for model_path in models:
        model_file = Path(model_path)
        if not model_file.is_file():
            print(f"[WARN] Model not found: {model_file}, skipping.", file=sys.stderr)
            continue
            
        model_name = model_file.stem
        print(f"\n[BENCH] Running roofline benchmark on {model_name}...")
        
        t_str = ",".join(str(t) for t in threads)
        p_str = ",".join(str(p) for p in p_lens)
        n_str = ",".join(str(n) for n in n_gens)
        
        cmd = [
            str(LLAMA_BENCH),
            "-m", str(model_file),
            "-t", t_str,
            "-p", p_str,
            "-n", n_str,
            "-r", str(reps),
            "-o", "json"
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            bench_json = json.loads(res.stdout)
            results.extend(bench_json)
            print(f"[SUCCESS] Completed {model_name}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] llama-bench failed for {model_name}: {e.stderr}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON output: {e}", file=sys.stderr)

    out_file = RESULTS_DIR / "roofline_bench.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved raw roofline results to {out_file}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run roofline benchmarks across SLM models.")
    parser.add_argument("--models", nargs="*", help="Specific GGUF models to benchmark")
    parser.add_argument("--threads", nargs="*", type=int, default=[1, 2, 3, 4])
    parser.add_argument("--prompt-len", nargs="*", type=int, default=[512])
    parser.add_argument("--gen-len", nargs="*", type=int, default=[128])
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args()

    if not args.models:
        # Default to all models in models/
        model_paths = list(MODELS_DIR.glob("*.gguf"))
    else:
        model_paths = [Path(m) for m in args.models]

    if not model_paths:
        print(f"No GGUF models found in {MODELS_DIR}. Run scripts/download_models.sh first.", file=sys.stderr)
        sys.exit(1)

    run_roofline(model_paths, threads=args.threads, p_lens=args.prompt_len, n_gens=args.gen_len, reps=args.reps)

if __name__ == "__main__":
    main()
