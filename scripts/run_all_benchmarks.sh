#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET="${1:-pi4}"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/benchmark_${TARGET}_${TIMESTAMP}.log"
LATEST_LOG="${LOG_DIR}/latest.log"

# If not already piping into tee, re-exec with tee logging
if [[ "${BENCH_LOGGING:-0}" != "1" ]]; then
    export BENCH_LOGGING=1
    ln -sf "${LOG_FILE}" "${LATEST_LOG}"
    echo "Logging complete session output to: ${LOG_FILE}"
    echo "Symlinked to: ${LATEST_LOG}"
    exec "$0" "$@" 2>&1 | tee "${LOG_FILE}"
fi

echo "=== [1/4] Checking / Building llama.cpp for ${TARGET} ==="
if [[ ! -f "${ROOT_DIR}/bin/llama-cli" || ! -f "${ROOT_DIR}/bin/llama-bench" ]]; then
    "${SCRIPT_DIR}/build_llama_cpp.sh" "${TARGET}"
fi

echo "=== [2/4] Downloading Baseline Fast Tier Models ==="
"${SCRIPT_DIR}/download_models.sh" "fast"

echo "=== [3/4] Executing Benchmark Suite ==="
echo "--> Running Roofline Benchmark..."
python3 "${ROOT_DIR}/src/bench_roofline.py" --threads 3 4

echo "--> Running JSON / Tool Calling Reliability Eval..."
python3 "${ROOT_DIR}/src/eval_json_tools.py" --threads 3

echo "--> Running Prompt Cache & TTFT Eval..."
python3 "${ROOT_DIR}/src/eval_prompt_cache.py" || true

echo "--> Running Speculative Decoding Eval..."
python3 "${ROOT_DIR}/src/eval_speculative.py" --threads 3 || true

echo "=== [4/4] Compiling Benchmark Report ==="
python3 "${ROOT_DIR}/src/generate_report.py"

echo "=== Finished Benchmarking ==="
echo "Report is available at: ${ROOT_DIR}/results/BENCHMARK_REPORT.md"
echo "Full raw console log is available at: ${LOG_FILE}"
