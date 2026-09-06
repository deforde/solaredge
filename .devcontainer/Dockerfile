FROM ubuntu:26.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc-arm-linux-gnueabihf \
    g++-arm-linux-gnueabihf \
    clangd \
    cmake \
    make && \
    rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/arm-linux-gnueabihf-gcc 100 \
    --slave /usr/bin/g++ g++ /usr/bin/arm-linux-gnueabihf-g++
