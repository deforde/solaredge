#!/usr/bin/env bash
set -eou pipefail

if [ ! -d "duckdb-python" ]; then
    echo "Cloning duckdb-python repository..."
    git clone --recurse-submodules https://github.com/duckdb/duckdb-python.git
fi

mkdir -p /workspace/.cache/pip
if [ ! -x /workspace/.venv/bin/python ]; then
    python3 -m venv /workspace/.venv
fi

# Install build requirements for the native container Python before setting the
# ARM wheel tag. This prevents pip from trying to build an ARM CMake package.
/workspace/.venv/bin/python -m pip install \
    --cache-dir /workspace/.cache/pip \
    build \
    "cmake>=3.29.0" \
    "ninja>=1.10" \
    "scikit-build-core>=0.11.4" \
    "nanobind>=3.0" \
    "numpy>=2.0"

cd duckdb-python

# Tell Python's wheel builder the exact architecture tag for the BeagleBone Black
export _PYTHON_HOST_PLATFORM=linux-armv7l
# Keep build dependencies and CMake output in the mounted workspace.
export PIP_CACHE_DIR=/workspace/.cache/pip
# Cross-compile the DuckDB extension for the BeagleBone Black. Do not export
# CC/CXX globally: build dependencies such as patchelf must run on the host.
export SKBUILD_CMAKE_ARGS="-DCMAKE_C_COMPILER=arm-linux-gnueabihf-gcc;-DCMAKE_CXX_COMPILER=arm-linux-gnueabihf-g++;-DCMAKE_SYSTEM_NAME=Linux;-DCMAKE_SYSTEM_PROCESSOR=armv7;-DDUCKDB_EXTRA_LINK_FLAGS=-latomic;-DDISABLE_UNITY=1"

echo "Building DuckDB Python wheel for 32-bit ARM..."
/workspace/.venv/bin/python -m build --wheel --no-isolation
