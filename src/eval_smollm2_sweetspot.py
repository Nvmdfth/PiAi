#!/usr/bin/env python3
"""Empirical test suite to determine optimal sampling parameters & sweet spots for SmolLM2-135M."""

import json
import time
import urllib.request
import urllib.error

ENDPOINT = "http://127.0.0.1:8080/completion"
MODEL = "smollm2-135m-q4_0"

def query_model(prompt, temperature=0.0, repeat_penalty=1.0, top_p=0.95, min_p=0.05, n_predict=48, grammar=""):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "temperature": temperature,
        "repeat_penalty": repeat_penalty,
        "top_p": top_p,
        "min_p": min_p,
        "n_predict": n_predict,
        "stop": ["\n\n", "<|im_end|>", "<|endoftext|>"]
    }
    if grammar:
        payload["grammar"] = grammar
        
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=data, headers={"Content-Type": "application/json"})
    
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - start
            return {
                "text": res.get("content", "").strip(),
                "tok_per_sec": res.get("timings", {}).get("predicted_per_second", 0),
                "tokens_predicted": res.get("tokens_predicted", 0),
                "tokens_evaluated": res.get("tokens_evaluated", 0),
                "elapsed": elapsed
            }
    except Exception as e:
        return {"text": f"ERROR: {e}", "tok_per_sec": 0, "tokens_predicted": 0, "elapsed": 0}

def run_tests():
    print("=== SmolLM2-135M Empirical Sweet Spot Benchmark ===")
    
    # 1. Temperature Sweep on Factoid / Classification
    print("\n--- 1. Temperature Sweep on Fast Factoid & Classification ---")
    prompt_fact = "Q: What port does SSH use?\nA:"
    for temp in [0.0, 0.2, 0.5, 0.8, 1.2]:
        res = query_model(prompt_fact, temperature=temp, n_predict=24)
        print(f"Temp={temp:0.1f} | Speed: {res['tok_per_sec']:5.1f} tok/s | Output: {res['text']}")

    # 2. Repetition Penalty Sweep on Repetition / Coherence
    print("\n--- 2. Repetition Penalty Sweep on Short Explanation ---")
    prompt_rep = "Explain what a CPU cache is in one simple sentence:"
    for rep in [1.0, 1.05, 1.10, 1.25, 1.50]:
        res = query_model(prompt_rep, temperature=0.2, repeat_penalty=rep, n_predict=40)
        print(f"RepeatPenalty={rep:0.2f} | Output: {res['text']}")

    # 3. Intent Routing / Classification Tasks
    print("\n--- 3. Intent Classification / Routing Accuracy ---")
    queries = [
        ("What is the memory usage on devpi?", "sysinfo"),
        ("Deploy docker compose on worker 2", "docker"),
        ("Will it rain tomorrow in Seattle?", "weather"),
        ("Reboot the server immediately", "system_control")
    ]
    
    classes = 'root ::= "sysinfo" | "docker" | "weather" | "system_control" | "unknown"'
    print("\n[A] With GBNF Constrained Grammar:")
    for query, expected in queries:
        prompt = f"<|im_start|>system\nClassify intent into: sysinfo, docker, weather, system_control.<|im_end|>\n<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"
        res = query_model(prompt, temperature=0.0, n_predict=16, grammar=classes)
        match = "MATCH" if res['text'].strip() == expected else "MISMATCH"
        print(f"Query: '{query}' -> [{res['text']}] ({match}) | Speed: {res['tok_per_sec']:5.1f} tok/s")

    print("\n[B] Without Grammar (Unconstrained Free-form):")
    for query, expected in queries:
        prompt = f"<|im_start|>system\nClassify intent into one word: sysinfo, docker, weather, system_control.<|im_end|>\n<|im_start|>user\n{query}<|im_end|>\n<|im_start|>assistant\n"
        res = query_model(prompt, temperature=0.0, n_predict=24)
        print(f"Query: '{query}' -> [{res['text']}]")

    # 4. JSON Key-Value Extraction with Grammar
    print("\n--- 4. Micro Structured Data Extraction with GBNF ---")
    json_grammar = r'''
    root ::= "{" ws "\"target\":" ws string "," ws "\"action\":" ws string "}"
    string ::= "\"" [^"\\]* "\""
    ws ::= [ \t\n]*
    '''
    prompt_extract = '<|im_start|>system\nExtract target and action into JSON: {"target": "...", "action": "..."}<|im_end|>\n<|im_start|>user\nRestart container nginx-proxy on node 1<|im_end|>\n<|im_start|>assistant\n'
    res = query_model(prompt_extract, temperature=0.0, n_predict=48, grammar=json_grammar)
    print(f"GBNF JSON Output: {res['text']} | Speed: {res['tok_per_sec']:5.1f} tok/s")

    # 5. Long-Form / Complex Coding Stress Test (Failure Boundary Test)
    print("\n--- 5. Complex Task Stress Test (Testing Failure Boundary) ---")
    prompt_code = "<|im_start|>user\nWrite a complete Python script using multiprocessing to parallelize image resizing with PIL.<|im_end|>\n<|im_start|>assistant\n"
    res = query_model(prompt_code, temperature=0.2, n_predict=64)
    print(f"Complex Code Generation (First 64 tokens):\n{res['text']}")

if __name__ == "__main__":
    run_tests()
