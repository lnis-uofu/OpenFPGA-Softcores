#!/bin/bash

[ -z $PROJECT_PATH ] && echo "[ERROR] source the 'setup_env.sh' first!" && exit 1

# Default script parameters
softcore="picorv32"
fpga_arch="${PROJECT_PATH}/fpga_archs/k6_frac_N10_adder_chain_dpram8K_dsp36_40nm.conf"
common_params="--device-layout 40x40 --isa im"
output_dir="fpga40x40_dpram8K_dsp36_CS"

# Soft-core argument
[ $# -ge 1 ] && softcore="$1"
echo "[INFO] Softcore: '$softcore'"

# FPGA architecture argument
[ $# -ge 2 ] && fpga_arch="$2"
echo "[INFO] FPGA Architecture: '$fpga_arch'"

# Run simulations
${PROJECT_TOOLS_PATH}/run_softcore.py \
    $softcore \
    $fpga_arch \
    $common_params \
    --run-tests ${PROJECT_PATH}/tests/cache_size_sweep_params.csv \
    --run-dir ${PROJECT_PATH}/run_dir/${output_dir}
