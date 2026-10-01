#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET="${1:-pi4}"
if [[ "$TARGET" == "pi5" ]]; then
    source "${ROOT_DIR}/configs/env_pi5.sh"
else
    source "${ROOT_DIR}/configs/env_pi4.sh"
fi

LLAMA_DIR="${ROOT_DIR}/llama.cpp"
BUILD_DIR="${ROOT_DIR}/build-${PI_TARGET}"
BIN_DIR="${ROOT_DIR}/bin/${PI_TARGET}"

mkdir -p "${BIN_DIR}"

if [[ ! -d "${LLAMA_DIR}" ]]; then
    echo "Cloning llama.cpp..."
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git "${LLAMA_DIR}"
else
    echo "llama.cpp repository exists at ${LLAMA_DIR}"
fi

echo "Configuring cmake for target: ${PI_TARGET} with flags: ${CMAKE_BUILD_FLAGS}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

cmake "${LLAMA_DIR}" \
    -DCMAKE_BUILD_TYPE=Release \
    ${CMAKE_BUILD_FLAGS}

echo "Building binaries (parallel cores: ${CPU_CORES})..."
cmake --build . --config Release -j"${CPU_CORES}" --target llama-cli llama-bench llama-server llama-speculative

echo "Copying binaries to ${BIN_DIR}..."
for b in llama-cli llama-bench llama-server llama-speculative; do
    if [[ -f "${BUILD_DIR}/bin/${b}" ]]; then
        cp -f "${BUILD_DIR}/bin/${b}" "${BIN_DIR}/${b}"
        chmod +x "${BIN_DIR}/${b}"
    fi
done

# Symlink to bin/ for default invocation
mkdir -p "${ROOT_DIR}/bin"
for b in llama-cli llama-bench llama-server llama-speculative; do
    if [[ -f "${BIN_DIR}/${b}" ]]; then
        ln -sf "${BIN_DIR}/${b}" "${ROOT_DIR}/bin/${b}"
    fi
done

echo "Build completed successfully. Binaries available in ${BIN_DIR}:"
ls -la "${BIN_DIR}"
