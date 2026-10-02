#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODELS_DIR="${ROOT_DIR}/models"

mkdir -p "${MODELS_DIR}"

declare -A MODEL_URLS=(
    ["smollm2-135m-q4_0"]="https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_0.gguf"
    ["smollm2-360m-q4_0"]="https://huggingface.co/bartowski/SmolLM2-360M-Instruct-GGUF/resolve/main/SmolLM2-360M-Instruct-Q4_0.gguf"
    ["smollm2-1.7b-q4_0"]="https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF/resolve/main/SmolLM2-1.7B-Instruct-Q4_0.gguf"
    ["qwen2.5-0.5b-q4_0"]="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf"
    ["qwen2.5-1.5b-q4_0"]="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_0.gguf"
    ["qwen2.5-3b-q4_0"]="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_0.gguf"
    ["qwen2.5-coder-0.5b-q4_0"]="https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_0.gguf"
    ["qwen2.5-coder-1.5b-q4_0"]="https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_0.gguf"
    ["llama-3.2-1b-q4_0"]="https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_0.gguf"
    ["gemma-4-e2b-it-q4_k_m"]="https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf"
)

download_model() {
    local key="$1"
    local url="${MODEL_URLS[$key]}"
    local filename="${key}.gguf"
    local dest="${MODELS_DIR}/${filename}"

    if [[ -f "${dest}" ]]; then
        echo "[EXISTS] ${filename} already in ${MODELS_DIR}"
        return 0
    fi

    echo "[DOWNLOADING] ${key} from ${url}..."
    curl -L -C - -f -o "${dest}.tmp" "${url}"
    mv "${dest}.tmp" "${dest}"
    echo "[COMPLETED] Downloaded ${filename} ($(du -h "${dest}" | cut -f1))"
}

TARGET_KEY="${1:-fast}"

if [[ "${TARGET_KEY}" == "all" ]]; then
    for key in "${!MODEL_URLS[@]}"; do
        download_model "${key}"
    done
elif [[ "${TARGET_KEY}" == "fast" ]]; then
    # Standard fast set
    download_model "smollm2-135m-q4_0"
    download_model "qwen2.5-0.5b-q4_0"
    download_model "qwen2.5-1.5b-q4_0"
    download_model "qwen2.5-coder-0.5b-q4_0"
    download_model "qwen2.5-coder-1.5b-q4_0"
else
    if [[ -n "${MODEL_URLS[$TARGET_KEY]+set}" ]]; then
        download_model "${TARGET_KEY}"
    else
        echo "Error: Unknown model key '${TARGET_KEY}'. Available:"
        for k in "${!MODEL_URLS[@]}"; do
            echo "  - $k"
        done
        exit 1
    fi
fi

echo "All requested models are ready in ${MODELS_DIR}."
