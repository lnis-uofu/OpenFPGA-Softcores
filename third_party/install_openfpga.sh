#!/bin/sh

git submodule update --init third_party/OpenFPGA
cd third_party/OpenFPGA
make all -j$(nproc)
cd -

