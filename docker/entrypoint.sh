#!/usr/bin/env sh
set -e

MODELS_DIR="${LLAMA_ARG_MODELS_DIR:-/models}"

if [ -d "$MODELS_DIR" ]; then
    echo "Checking models in $MODELS_DIR..."

    download_if_missing() {
        NAME="$1"
        URL="$2"
        DEST="$MODELS_DIR/$NAME"
        if [ ! -f "$DEST" ]; then
            echo "Downloading $NAME from $URL..."
            if curl -L -C - -f --retry 3 --retry-delay 3 --connect-timeout 15 -o "$DEST.tmp" "$URL"; then
                # Verify GGUF magic header
                if [ "$(head -c 4 "$DEST.tmp" 2>/dev/null)" = "GGUF" ]; then
                    mv "$DEST.tmp" "$DEST"
                    echo "Successfully downloaded $NAME"
                else
                    echo "Warning: Downloaded file $NAME did not match GGUF header. Removing temporary file."
                    rm -f "$DEST.tmp"
                fi
            else
                echo "Warning: Failed to download $NAME from $URL (network error). Skipping."
                rm -f "$DEST.tmp"
            fi
        fi
    }

    download_if_missing "qwen2.5-0.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf"
    download_if_missing "qwen2.5-coder-0.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_0.gguf"
    download_if_missing "qwen2.5-1.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_0.gguf"
    download_if_missing "qwen2.5-coder-1.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_0.gguf"
    download_if_missing "smollm2-135m-q4_0.gguf" "https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_0.gguf"
    download_if_missing "gemma-3-4b-it-q4_k_m.gguf" "https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf"
else
    echo "Warning: Models directory $MODELS_DIR does not exist. Skipping auto-download."
fi

echo "Starting llama-server multi-model router on port ${LLAMA_ARG_PORT:-8080}..."
exec /usr/local/bin/llama-server "$@"
