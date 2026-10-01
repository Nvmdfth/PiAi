#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET="${1:-pi4}"

echo "=== 1. Checking / Building llama.cpp for ${TARGET} ==="
if [[ ! -f "${ROOT_DIR}/bin/llama-cli" || ! -f "${ROOT_DIR}/bin/llama-bench" ]]; then
    "${SCRIPT_DIR}/build_llama_cpp.sh" "${TARGET}"
fi

echo "=== 2. Downloading Baseline Fast Tier Models ==="
"${SCRIPT_DIR}/download_models.sh" "fast"

echo "=== 3. Executing Benchmark Suite ==="
echo "--> Running Roofline Benchmark..."
python3 "${ROOT_DIR}/src/bench_roofline.py" --threads 3 4

echo "--> Running JSON / Tool Calling Reliability Eval..."
python3 "${ROOT_DIR}/src/eval_json_tools.py" --threads 3

echo "--> Running Prompt Cache & TTFT Eval..."
python3 "${ROOT_DIR}/src/eval_prompt_cache.py" --threads 3

echo "--> Running Speculative Decoding Eval..."
python3 "${ROOT_DIR}/src/eval_speculative.py" --threads 3 || true

echo "=== 4. Compiling Benchmark Report ==="
python3 "${ROOT_DIR}/src/generate_report.py"

echo "=== Finished Benchmarking ==="
echo "Report is available at: ${ROOT_DIR}/results/BENCHMARK_REPORT.md"
