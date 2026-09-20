#!/usr/bin/env bash
set -eou pipefail

if [ ! -d "duckdb-python" ]; then
    echo "Cloning duckdb-python repository..."
    git clone --recurse-submodules https://github.com/duckdb/duckdb-python.git
    cd duckdb-python
    git fetch --tags
    git checkout v1.5.5
    git submodule update --init --recursive
    cd ..
fi

mkdir -p /workspace/.cache/pip
if [ ! -x /workspace/.venv/bin/python ] || \
    ! /workspace/.venv/bin/python -c 'import sys, pip; assert sys.version_info[:2] == (3, 13)' 2>/dev/null; then
    rm -rf /workspace/.venv
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
    "pybind11[global]>=2.6.0" \
    "setuptools-scm>=8.0" \
    "nanobind>=3.0" \
    "numpy>=2.0"

# The pip cmake package keeps its executable under site-packages rather than
# installing it in the system PATH. Prefer it over Debian's older CMake.
export PATH="$(/workspace/.venv/bin/python -c 'import cmake, os; print(os.path.join(os.path.dirname(cmake.__file__), "data", "bin"))'):${PATH}"

cd duckdb-python

# Tell Python's wheel builder the exact architecture tag for the BeagleBone Black
export _PYTHON_HOST_PLATFORM=linux-armv7l
# Keep build dependencies and CMake output in the mounted workspace.
export PIP_CACHE_DIR=/workspace/.cache/pip
# Cross-compile the DuckDB extension for the BeagleBone Black. Do not export
# CC/CXX globally: build dependencies such as patchelf must run on the host.
export SKBUILD_CMAKE_ARGS="-DCMAKE_C_COMPILER=arm-linux-gnueabihf-gcc;-DCMAKE_CXX_COMPILER=arm-linux-gnueabihf-g++;-DCMAKE_SYSTEM_NAME=Linux;-DCMAKE_SYSTEM_PROCESSOR=armv7;-DDUCKDB_EXTRA_LINK_FLAGS=-latomic;-DDISABLE_UNITY=1;-DPython_INCLUDE_DIR=/opt/bbb-sysroot/usr/include/python3.13;-DPython_LIBRARY=/opt/bbb-sysroot/usr/lib/arm-linux-gnueabihf/libpython3.13.so"

echo "Building DuckDB Python wheel for 32-bit ARM..."
/workspace/.venv/bin/python -m build \
    --wheel \
    --no-isolation \
    --config-setting=build-dir=/workspace/duckdb-python/build/cpython-313
