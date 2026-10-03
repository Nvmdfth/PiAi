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

    # pi4 is limited to the 1.5B models plus the shared 0.5B draft; pi5 adds the rest
    download_if_missing "qwen2.5-0.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf"
    download_if_missing "qwen2.5-1.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_0.gguf"
    download_if_missing "qwen2.5-coder-1.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_0.gguf"
    if [ "${PIAI_PROFILE:-pi4}" = "pi5" ]; then
        download_if_missing "qwen2.5-coder-0.5b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_0.gguf"
        download_if_missing "qwen2.5-3b-q4_0.gguf" "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_0.gguf"
        download_if_missing "smollm2-135m-q4_0.gguf" "https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/main/SmolLM2-135M-Instruct-Q4_0.gguf"
        download_if_missing "gemma-4-e2b-it-q4_k_m.gguf" "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf"
    fi
else
    echo "Warning: Models directory $MODELS_DIR does not exist. Skipping auto-download."
fi

SLOT_DIR="/slots"
API="http://127.0.0.1:${LLAMA_ARG_PORT:-8080}"

# Persist each loaded model's busiest KV slot across restarts, so the first request
# after a restart skips the cold prefix. A saved cache is only reused when the model
# file and the preset (ctx size, KV type, ...) match what it was saved under.
slot_fingerprint() {
    echo "$(stat -c '%s-%Y' "$MODELS_DIR/$1.gguf" 2>/dev/null) $(md5sum < /configs/models_preset.ini | cut -d' ' -f1)"
}

loaded_models() {
    curl -s -m 5 "$API/v1/models" | sed 's/{"id"/\n&/g' | grep '"value":"loaded"' \
        | sed 's/^{"id":"\([^"]*\)".*/\1/'
}

# Prints "<prompt tokens> <slot id>" for the slot holding the longest prompt
busiest_slot() {
    curl -s -m 5 "$API/slots?model=$1" | sed 's/{"id":/\n&/g' \
        | sed -n 's/^{"id":\([0-9]*\),.*"n_prompt_tokens":\([0-9]*\).*/\2 \1/p' | sort -n | tail -n 1
}

save_slots() {
    [ -d "$SLOT_DIR" ] || return 0
    for id in $(loaded_models); do
        slot="$(busiest_slot "$id")"
        [ -n "$slot" ] || continue
        out="$(curl -s -m 20 -X POST "$API/slots/${slot#* }?action=save" -H 'Content-Type: application/json' \
            -d "{\"model\":\"$id\",\"filename\":\"$id.bin\"}")"
        case "$out" in
            *n_saved*) slot_fingerprint "$id" > "$SLOT_DIR/$id.meta"; echo "slot cache saved: $id" ;;
            *) echo "slot cache save failed: $id: $out" ;;
        esac
    done
}

restore_slots() {
    until curl -sf -m 2 "$API/health" > /dev/null; do sleep 2; done
    for meta in "$SLOT_DIR"/*.meta; do
        [ -e "$meta" ] || return 0
        id="$(basename "$meta" .meta)"
        if [ "$(cat "$meta")" != "$(slot_fingerprint "$id")" ]; then
            echo "slot cache stale, skipping: $id"
            continue
        fi
        out="$(curl -s -m 600 -X POST "$API/slots/0?action=restore" -H 'Content-Type: application/json' \
            -d "{\"model\":\"$id\",\"filename\":\"$id.bin\"}")"
        case "$out" in
            *n_restored*) echo "slot cache restored: $id" ;;
            *) echo "slot cache restore failed: $id: $out" ;;
        esac
    done
}

echo "Starting llama-server multi-model router on port ${LLAMA_ARG_PORT:-8080}..."
/usr/local/bin/llama-server "$@" &
SERVER_PID=$!

restore_slots &
RESTORE_PID=$!

on_stop() {
    kill "$RESTORE_PID" 2>/dev/null || true
    save_slots
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" || true
    exit 0
}
trap on_stop TERM INT

wait "$SERVER_PID"
