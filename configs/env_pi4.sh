#!/usr/bin/env bash
# Hardware environment settings for Raspberry Pi 4 Model B (Cortex-A72)

export PI_TARGET="pi4"
export CPU_CORES=4
export OPTIMAL_THREADS=3
export CMAKE_BUILD_FLAGS="-DGGML_NATIVE=ON -DGGML_LTO=ON -DGGML_OPENMP=ON"
