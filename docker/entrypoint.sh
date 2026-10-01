#!/usr/bin/env sh
set -e

# Default model download URLs if file doesn't exist on mounted volume
MODEL_FILE="${LLAMA_ARG_MODEL:-/models/qwen2.5-0.5b-q4_0.gguf}"

if [ ! -f "$MODEL_FILE" ]; then
    echo "=============================================================="
    echo "Model file '$MODEL_FILE' not found on mounted volume."
    echo "=============================================================="

    case "$MODEL_FILE" in
        *qwen2.5-0.5b*)
            URL="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf"
            ;;
        *qwen2.5-1.5b*)
            URL="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_0.gguf"
            ;;
        *qwen2.5-3b*)
            URL="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_0.gguf"
            ;;
        *smollm2-135m*)
            URL="https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_0.gguf"
            ;;
        *smollm2-1.7b*)
            URL="https://huggingface.co/bartowski/SmolLM2-1.7B-Instruct-GGUF/resolve/main/SmolLM2-1.7B-Instruct-Q4_0.gguf"
            ;;
        *llama-3.2-1b*)
            URL="https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_0.gguf"
            ;;
        *)
            if [ -n "$MODEL_DOWNLOAD_URL" ]; then
                URL="$MODEL_DOWNLOAD_URL"
            else
                echo "Error: Cannot auto-download '$MODEL_FILE'. Provide a model in ./models or set MODEL_DOWNLOAD_URL."
                exit 1
            fi
            ;;
    esac

    DIRNAME="$(dirname "$MODEL_FILE")"
    mkdir -p "$DIRNAME" 2>/dev/null || true
    echo "Downloading default model from: $URL..."
    curl -L -C - -f -o "$MODEL_FILE.tmp" "$URL"
    mv "$MODEL_FILE.tmp" "$MODEL_FILE"
    echo "Model downloaded successfully to $MODEL_FILE"
fi

echo "Starting llama-server with model: $MODEL_FILE on port ${LLAMA_ARG_PORT:-8080}..."
exec /usr/local/bin/llama-server "$@"
