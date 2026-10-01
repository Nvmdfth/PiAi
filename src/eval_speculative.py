#!/usr/bin/env python3
"""
eval_speculative.py: Evaluates speculative decoding performance
comparing standalone model decode vs draft-accelerated decode.
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
RESULTS_DIR = ROOT_DIR / "results" / "raw"

LLAMA_SPECULATIVE = BIN_DIR / "llama-speculative"
LLAMA_CLI = BIN_DIR / "llama-cli"

TEST_PROMPT = "Write a Python function to compute the moving average of a streaming list of numbers, handling edge cases."

def parse_tok_per_sec(stderr_text):
    # eval time = 1234.56 ms / 64 runs ( 19.29 ms per token, 51.84 tokens per second)
    m = re.search(r"eval time\s*=.*?([\d\.]+)\s*tokens per second", stderr_text)
    if m:
        return float(m.group(1))
    return 0.0

def run_speculative_test(target_model, draft_model, draft_k=4, threads=3, n_tokens=64):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    t_file = Path(target_model)
    d_file = Path(draft_model)

    if not t_file.is_file() or not d_file.is_file():
        print(f"[WARN] Target or draft model file missing: {t_file} / {d_file}", file=sys.stderr)
        return None

    print(f"\n[EVAL] Testing speculative decoding: Target={t_file.stem}, Draft={d_file.stem}...")

    # 1. Standalone Target Baseline
    cmd_base = [
        str(LLAMA_CLI),
        "-m", str(t_file),
        "-p", TEST_PROMPT,
        "-n", str(n_tokens),
        "-t", str(threads),
        "--no-display-prompt",
        "--no-conversation"
    ]
    
    start_base = time.time()
    res_base = subprocess.run(cmd_base, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    lat_base = time.time() - start_base
    base_tps = parse_tok_per_sec(res_base.stderr)
    if base_tps == 0.0 and lat_base > 0 and res_base.returncode == 0:
        base_tps = round(n_tokens / lat_base, 2)

    # 2. Speculative Run
    cmd_spec = [
        str(LLAMA_SPECULATIVE),
        "-m", str(t_file),
        "-md", str(d_file),
        "-p", TEST_PROMPT,
        "-n", str(n_tokens),
        "-t", str(threads),
        "--draft-max", str(draft_k)
    ]
    
    start_spec = time.time()
    res_spec = subprocess.run(cmd_spec, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    lat_spec = time.time() - start_spec
    spec_tps = parse_tok_per_sec(res_spec.stderr)
    if spec_tps == 0.0 and lat_spec > 0 and res_spec.returncode == 0:
        spec_tps = round(n_tokens / lat_spec, 2)

    speedup = round(spec_tps / base_tps, 2) if base_tps > 0 else 1.0

    print(f"  Standalone: {base_tps} tok/s | Speculative: {spec_tps} tok/s | Speedup: {speedup}x")

    return {
        "target_model": t_file.name,
        "draft_model": d_file.name,
        "draft_k": draft_k,
        "threads": threads,
        "returncode_base": res_base.returncode,
        "returncode_spec": res_spec.returncode,
        "baseline_tok_per_s": base_tps,
        "speculative_tok_per_s": spec_tps,
        "speedup_factor": speedup
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate speculative decoding acceleration.")
    parser.add_argument("--target", help="Path to target model GGUF")
    parser.add_argument("--draft", help="Path to draft model GGUF")
    parser.add_argument("--draft-k", type=int, default=4)
    parser.add_argument("--threads", type=int, default=3)
    args = parser.parse_args()

    if not LLAMA_SPECULATIVE.is_file():
        print(f"llama-speculative binary not found at {LLAMA_SPECULATIVE}.", file=sys.stderr)
        sys.exit(0)

    pairs = []
    if args.target and args.draft:
        pairs.append((args.target, args.draft))
    else:
        # Standard pairing candidates
        candidates = [
            (MODELS_DIR / "smollm2-1.7b-q4_0.gguf", MODELS_DIR / "smollm2-135m-q4_0.gguf"),
            (MODELS_DIR / "qwen2.5-1.5b-q4_0.gguf", MODELS_DIR / "qwen2.5-0.5b-q4_0.gguf"),
            (MODELS_DIR / "qwen2.5-3b-q4_0.gguf", MODELS_DIR / "qwen2.5-0.5b-q4_0.gguf")
        ]
        for t, d in candidates:
            if t.exists() and d.exists():
                pairs.append((str(t), str(d)))

    results = []
    for t_path, d_path in pairs:
        r = run_speculative_test(t_path, d_path, draft_k=args.draft_k, threads=args.threads)
        if r:
            results.append(r)

    out_file = RESULTS_DIR / "eval_speculative.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved speculative evaluation results to {out_file}")

if __name__ == "__main__":
    main()
