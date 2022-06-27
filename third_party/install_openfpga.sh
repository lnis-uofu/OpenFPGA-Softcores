#!/bin/sh

# Curently OpenFPGA is supported for
# - Ubuntu >= 18.04
# - Red Hat >= 7.5

os=$(lsb_release -si)
version=$(lsb_release -sr)
if [[ ! $os =~ "RedHat" ]] && [[ ! $os =~ "Ubuntu" ]]; then
    echo "[ERROR] OpenFPGA is only supported for RedHat or Ubuntu platforms!"
    exit 1
fi
if [[ $os =~ "RedHat" ]] && [[ $version < "7.5" ]]; then
    echo "[ERROR] OpenFPGA is only supported for RedHat >= 7.5!"
    exit 2
fi
if [[ $os =~ "Ubuntu" ]] && [[ $version < "18.04" ]]; then
    echo "[ERROR] OpenFPGA is only supported for Ubuntu >= 18.04!"
    exit 2
fi

# Dependencies: bison, flex, libreadline-dev, libffi-dev, tcllib, swig, ...
# Full list: OpenFPGA/.github/workflows/install_dependencies_build.sh

git submodule update --init third_party/OpenFPGA
cd third_party/OpenFPGA
make all -j$(nproc)
cd -

