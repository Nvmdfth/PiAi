#!/usr/bin/env python3
"""
eval_prompt_cache.py: Evaluates cold vs warm Time To First Token (TTFT)
and prompt processing latency using the llama-server slot prefix cache.

Requires a running llama-server (default http://localhost:8080). llama-cli no
longer accepts --prompt-cache, so the server is the only path that caches.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT_DIR / "results" / "raw"

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

REQUEST_TIMEOUT_S = 600

def api(server, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{server}{path}", data, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
        return json.load(resp)

def loaded_models(server):
    data = api(server, "/v1/models")["data"]
    return [m["id"] for m in data if m.get("status", {}).get("value") == "loaded"]

def timed_chat(server, model, system, query):
    body = {
        "model": model,
        "max_tokens": 32,
        "cache_prompt": True,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ],
    }
    start = time.time()
    timings = api(server, "/v1/chat/completions", body)["timings"]
    return time.time() - start, timings

def run_cache_benchmark(server, model):
    print(f"\n[EVAL] Testing prompt cache on {model}...")

    # A unique leading nonce guarantees the first request misses any cache left
    # by earlier runs; the second shares the whole prefix but asks something new.
    system = f"[run {uuid.uuid4().hex}]\n{SHARED_SYSTEM_PREFIX}"

    lat_cold, t_cold = timed_chat(server, model, system, QUERY_COLD)
    lat_warm, t_warm = timed_chat(server, model, system, QUERY_WARM)
    speedup = round(lat_cold / lat_warm, 2) if lat_warm > 0 else 1.0

    print(f"  Cold Wall: {lat_cold:.2f}s (Prompt: {t_cold['prompt_ms']:.1f}ms, {t_cold['prompt_n']} tok) | "
          f"Warm Wall: {lat_warm:.2f}s (Prompt: {t_warm['prompt_ms']:.1f}ms, {t_warm['prompt_n']} tok, "
          f"{t_warm.get('cache_n', 0)} cached) | Speedup: {speedup}x")

    return {
        "model": model,
        "cold_wall_latency_s": round(lat_cold, 3),
        "warm_wall_latency_s": round(lat_warm, 3),
        "cold_prompt_eval_ms": round(t_cold["prompt_ms"], 1),
        "warm_prompt_eval_ms": round(t_warm["prompt_ms"], 1),
        "cold_prompt_tokens": t_cold["prompt_n"],
        "warm_prompt_tokens": t_warm["prompt_n"],
        "warm_cached_tokens": t_warm.get("cache_n", 0),
        "speedup_factor": speedup,
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate prompt caching performance.")
    parser.add_argument("--server", default="http://localhost:8080", help="llama-server base URL")
    parser.add_argument("--models", nargs="*", help="Model ids to evaluate (default: loaded models)")
    args = parser.parse_args()

    try:
        models = args.models or loaded_models(args.server)
    except (urllib.error.URLError, OSError) as e:
        print(f"Error: llama-server not reachable at {args.server} ({e}).", file=sys.stderr)
        sys.exit(1)

    if not models:
        print("No loaded models reported by the server; pass --models.", file=sys.stderr)
        sys.exit(1)

    results = [run_cache_benchmark(args.server, m) for m in models]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / "eval_prompt_cache.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved prompt cache evaluation results to {out_file}")

if __name__ == "__main__":
    main()
