#!/usr/bin/env python3
"""
eval_json_tools.py: Evaluates JSON extraction and tool call reliability
comparing unconstrained generation vs GBNF-constrained generation.
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
GRAMMARS_DIR = ROOT_DIR / "grammars"
RESULTS_DIR = ROOT_DIR / "results" / "raw"

LLAMA_CLI = BIN_DIR / "llama-cli"

TEST_PROMPTS = [
    {
        "id": "iot_temperature_alert",
        "input": "System Sensor 4 reported temperature 89.4C at 14:02:11, which exceeds threshold 75C. Action required: alert security team.",
        "expected_action": "alert",
        "expected_target": "security team"
    },
    {
        "id": "server_restart",
        "input": "Service nginx-proxy is unresponsive (HTTP 502). Initiate immediate restart on node worker-02.",
        "expected_action": "restart",
        "expected_target": "nginx-proxy"
    },
    {
        "id": "disk_status_check",
        "input": "Query the current disk utilization and health status for storage volume vol-data-01.",
        "expected_action": "status",
        "expected_target": "vol-data-01"
    },
    {
        "id": "gpio_pin_write",
        "input": "Activate cooling fan relay on GPIO pin 18. Value set to high.",
        "expected_action": "write",
        "expected_target": "GPIO pin 18"
    },
    {
        "id": "sensor_telemetry_read",
        "input": "Read latest humidity and ambient pressure values from sensor BME280.",
        "expected_action": "read",
        "expected_target": "BME280"
    }
]

SYSTEM_PROMPT = """You are an edge system dispatcher. Given a system event, output ONLY a JSON object:
{
  "action": "read" | "write" | "restart" | "alert" | "status",
  "target": "<target string>",
  "parameters": {},
  "confidence": 0.95
}"""

def check_binary():
    if not LLAMA_CLI.is_file():
        print(f"Error: llama-cli binary not found at {LLAMA_CLI}.", file=sys.stderr)
        sys.exit(1)

def run_single_eval(model_path, grammar_file=None, threads=3):
    results = []
    
    for item in TEST_PROMPTS:
        prompt_text = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\n{item['input']}<|im_end|>\n<|im_start|>assistant\n"
        
        cmd = [
            str(LLAMA_CLI),
            "-m", str(model_path),
            "-p", prompt_text,
            "-n", "128",
            "-t", str(threads),
            "--temp", "0.1",
            "--no-display-prompt",
            "--no-conversation"
        ]
        
        if grammar_file and Path(grammar_file).is_file():
            cmd.extend(["--grammar-file", str(grammar_file)])

        start_time = time.time()
        res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
        latency = time.time() - start_time
        
        raw_output = res.stdout.strip()
        
        parsed_json = None
        is_valid_json = False
        action_match = False
        
        if res.returncode == 0:
            try:
                # Strip markdown codeblocks if model added them
                clean_str = re.sub(r"^```(?:json)?\s*", "", raw_output)
                clean_str = re.sub(r"```$", "", clean_str).strip()
                parsed_json = json.loads(clean_str)
                is_valid_json = True
                
                if isinstance(parsed_json, dict):
                    act = str(parsed_json.get("action", "")).lower()
                    if act == item["expected_action"]:
                        action_match = True
            except Exception:
                is_valid_json = False

        results.append({
            "test_id": item["id"],
            "returncode": res.returncode,
            "raw_output": raw_output,
            "is_valid_json": is_valid_json,
            "action_match": action_match,
            "latency_s": round(latency, 3),
            "parsed_json": parsed_json
        })
        
    return results

def eval_model(model_path, threads=3):
    check_binary()
    model_file = Path(model_path)
    if not model_file.is_file():
        print(f"[WARN] Model not found: {model_file}", file=sys.stderr)
        return None

    grammar_path = GRAMMARS_DIR / "tool_call.gbnf"
    print(f"\n[EVAL] Testing JSON extraction on {model_file.stem} (threads={threads})...")

    unconstrained_results = run_single_eval(model_file, grammar_file=None, threads=threads)
    grammar_results = run_single_eval(model_file, grammar_file=grammar_path, threads=threads)

    def summarize(res_list):
        total = len(res_list)
        valid_json = sum(1 for r in res_list if r["is_valid_json"])
        correct_action = sum(1 for r in res_list if r["action_match"])
        avg_lat = sum(r["latency_s"] for r in res_list) / total if total else 0
        return {
            "total_runs": total,
            "valid_json_count": valid_json,
            "valid_json_pct": round((valid_json / total) * 100, 1) if total else 0.0,
            "correct_action_count": correct_action,
            "correct_action_pct": round((correct_action / total) * 100, 1) if total else 0.0,
            "avg_latency_s": round(avg_lat, 3),
            "details": res_list
        }

    summary = {
        "model": model_file.name,
        "unconstrained": summarize(unconstrained_results),
        "grammar_constrained": summarize(grammar_results)
    }
    return summary

def main():
    parser = argparse.ArgumentParser(description="Evaluate structured JSON extraction reliability.")
    parser.add_argument("--models", nargs="*", help="Model paths to evaluate")
    parser.add_argument("--threads", type=int, default=3)
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not args.models:
        model_paths = list(MODELS_DIR.glob("*.gguf"))
    else:
        model_paths = [Path(m) for m in args.models]

    if not model_paths:
        print(f"No models found. Run scripts/download_models.sh first.", file=sys.stderr)
        sys.exit(1)

    all_summaries = []
    for m in model_paths:
        s = eval_model(m, threads=args.threads)
        if s:
            all_summaries.append(s)

    out_file = RESULTS_DIR / "eval_json_tools.json"
    with open(out_file, "w") as f:
        json.dump(all_summaries, f, indent=2)
    print(f"\nSaved structured tool evaluation results to {out_file}")

if __name__ == "__main__":
    main()
