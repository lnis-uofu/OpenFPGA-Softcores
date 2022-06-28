#!/bin/bash

[ -z $PROJECT_PATH ] && echo "[ERROR] source the 'setup_env.sh' first!" && exit 1

# Default script parameters
softcore="picorv32"
fpga_arch="${PROJECT_PATH}/fpga_archs/k6_frac_N10_adder_chain_dpram8K_dsp36_40nm.conf"
output_dir="fpga40x40_dpram8K_dsp36_BP"
common_params="--cache-size 65536 --isa im --run-dir ${PROJECT_PATH}/run_dir/${output_dir}"
tool="${PROJECT_TOOLS_PATH}/run_softcore.py"

# Soft-core argument
[ $# -ge 1 ] && softcore="$1"
echo "[INFO] Softcore: '$softcore'"

# FPGA architecture argument
[ $# -ge 2 ] && fpga_arch="$2"
echo "[INFO] FPGA Architecture: '$fpga_arch'"

# Run simulations
$tool $softcore $fpga_arch $common_params --device-layout 40x40_bram-s2r8_dsp-s6r8
$tool $softcore $fpga_arch $common_params --device-layout 40x40_bram-s2r6_dsp-s6r8
$tool $softcore $fpga_arch $common_params --device-layout 40x40_bram-s2r8_dsp-s3r12
$tool $softcore $fpga_arch $common_params --device-layout 40x40_bram-s2r6_dsp-s3r12
$tool $softcore $fpga_arch $common_params --device-layout 40x40_bram-s2r8_dsp-x20
$tool $softcore $fpga_arch $common_params --device-layout 40x40_bram-s2r6_dsp-x20

