#!/usr/bin/env python3
"""
generate_report.py: Aggregates raw benchmark JSONs and produces
an empirical Markdown scorecard in results/BENCHMARK_REPORT.md.
"""

import json
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "results" / "raw"
REPORT_FILE = ROOT_DIR / "results" / "BENCHMARK_REPORT.md"

def load_json(filename):
    p = RAW_DIR / filename
    if p.exists():
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            return None
    return None

def main():
    roofline_data = load_json("roofline_bench.json")
    json_tool_data = load_json("eval_json_tools.json")
    prompt_cache_data = load_json("eval_prompt_cache.json")
    speculative_data = load_json("eval_speculative.json")

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Small Language Model (SLM) Benchmark Report")
    lines.append(f"\n*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Section 1: Executive Summary
    lines.append("## 1. Executive Summary")
    has_data = any([roofline_data, json_tool_data, prompt_cache_data, speculative_data])
    if not has_data:
        lines.append("*No benchmark runs executed yet. Run `scripts/run_all_benchmarks.sh` to populate data.*\n")
    else:
        lines.append("- Empirical benchmarks collected across native ARM NEON inference on Cortex-A72.")
        if json_tool_data:
            lines.append("- Structured GBNF constrained decoding evaluated against raw unconstrained sampling.")
        if prompt_cache_data:
            lines.append("- System prompt caching evaluated for TTFT amortization across repeated queries.")
        if speculative_data:
            lines.append("- Speculative drafting evaluated for bandwidth amortization on small parameter models.")
        lines.append("\n")

    # Section 2: Roofline Throughput
    lines.append("## 2. Raw Generation & Prompt Processing (Roofline)")
    if roofline_data:
        lines.append("| Model | Threads | Test Type | Speed (tokens/sec) | Latency (ms/token) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: |")
        for item in roofline_data:
            model = Path(item.get("model_filename", item.get("model_type", "unknown"))).name
            threads = item.get("n_threads", "-")
            n_prompt = item.get("n_prompt", 0)
            n_gen = item.get("n_gen", 0)
            test_type = f"Prompt ({n_prompt}t)" if n_prompt > 0 else f"Gen ({n_gen}t)"
            
            # llama-bench json outputs avg_ts (tokens/sec)
            tok_per_sec = round(item.get("avg_ts", item.get("tg_avg", item.get("pp_avg", 0.0))), 2)
            ms_per_tok = round(1000.0 / tok_per_sec, 2) if tok_per_sec > 0 else "-"
            lines.append(f"| `{model}` | {threads} | {test_type} | **{tok_per_sec}** | {ms_per_tok} |")
    else:
        lines.append("*No raw roofline benchmark data recorded.*")

    lines.append("\n")

    # Section 3: JSON Tool Extraction
    lines.append("## 3. Headless JSON & Tool-Calling Reliability")
    if json_tool_data:
        lines.append("| Model | Unconstrained Valid % | Grammar Valid % | Action Match % | Avg Latency (s) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: |")
        for item in json_tool_data:
            model = item.get("model", "unknown")
            un = item.get("unconstrained", {})
            gr = item.get("grammar_constrained", {})
            lines.append(f"| `{model}` | {un.get('valid_json_pct', 0)}% | **{gr.get('valid_json_pct', 0)}%** | {gr.get('correct_action_pct', 0)}% | {gr.get('avg_latency_s', 0)}s |")
    else:
        lines.append("*No JSON tool evaluation data recorded.*")

    lines.append("\n")

    # Section 4: Prompt Cache
    lines.append("## 4. Prompt Caching & TTFT Acceleration")
    if prompt_cache_data:
        lines.append("| Model | Cold Latency (s) | Warm Latency (s) | Cold Prompt (ms) | Warm Prompt (ms) | Speedup Factor |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
        for item in prompt_cache_data:
            model = item.get("model", "unknown")
            cold = item.get("cold_wall_latency_s", 0)
            warm = item.get("warm_wall_latency_s", 0)
            c_p = item.get("cold_prompt_eval_ms", "-")
            w_p = item.get("warm_prompt_eval_ms", "-")
            speedup = item.get("speedup_factor", 1.0)
            lines.append(f"| `{model}` | {cold}s | **{warm}s** | {c_p} | {w_p} | **{speedup}x** |")
    else:
        lines.append("*No prompt cache data recorded.*")

    lines.append("\n")

    # Section 5: Speculative Decoding
    lines.append("## 5. Speculative Decoding Multiplier")
    if speculative_data:
        lines.append("| Target Model | Draft Model | Baseline (tok/s) | Speculative (tok/s) | Speedup |")
        lines.append("| :--- | :--- | :---: | :---: | :---: |")
        for item in speculative_data:
            t = item.get("target_model", "-")
            d = item.get("draft_model", "-")
            base = item.get("baseline_tok_per_s", 0)
            spec = item.get("speculative_tok_per_s", 0)
            sp = item.get("speedup_factor", 1.0)
            lines.append(f"| `{t}` | `{d}` | {base} | **{spec}** | **{sp}x** |")
    else:
        lines.append("*No speculative decoding data recorded.*")

    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Generated benchmark report at {REPORT_FILE}")

if __name__ == "__main__":
    main()
