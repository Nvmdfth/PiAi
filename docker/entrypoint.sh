#!/usr/bin/env sh
set -e

MODELS_DIR="${LLAMA_ARG_MODELS_DIR:-/models}"

# If models directory is enabled, ensure standard suite models exist
if [ -d "$MODELS_DIR" ]; then
    echo "Checking models in $MODELS_DIR..."

    download_if_missing() {
        NAME="$1"
        URL="$2"
        DEST="$MODELS_DIR/$NAME"
        if [ ! -f "$DEST" ]; then
            echo "Downloading $NAME from $URL..."
            curl -L -C - -f -o "$DEST.tmp" "$URL"
            mv "$DEST.tmp" "$DEST"
        fi
    }

    download_if_missing "qwen2.5-0.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf"
    download_if_missing "qwen2.5-coder-0.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_0.gguf"
    download_if_missing "qwen2.5-1.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_0.gguf"
    download_if_missing "qwen2.5-coder-1.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_0.gguf"
fi

echo "Starting llama-server multi-model router on port ${LLAMA_ARG_PORT:-8080}..."
exec /usr/local/bin/llama-server "$@"
