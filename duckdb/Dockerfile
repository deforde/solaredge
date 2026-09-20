FROM ubuntu:26.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc-arm-linux-gnueabihf \
    g++-arm-linux-gnueabihf \
    gcc \
    g++ \
    cmake \
    make \
    ninja-build \
    pkg-config \
    python3 \
    python3-dev \
    python3-venv \
    python-is-python3 \
    python3-pip \
    python3-build \
    python3-wheel \
    autoconf \
    automake \
    libtool \
    git && \
    rm -rf /var/lib/apt/lists/*
