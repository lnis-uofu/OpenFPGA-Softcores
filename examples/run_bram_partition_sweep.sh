#!/bin/bash

[ -z $PROJECT_PATH ] && echo "[ERROR] source the 'setup_env.sh' first!" && exit 1

# Default script parameters
softcore="picorv32"
fpga_arch="${PROJECT_PATH}/fpga_archs/k6_frac_N10_adder_chain_dpram8K_dsp36_40nm.conf"
output_name="fpga40x40_dpram8K_dsp36_BP"
common_params="--cache-size 65536 --isa im"

# Soft-core argument
[ $# -ge 1 ] && softcore="$1"
echo "[INFO] Softcore: '$softcore'"

# FPGA architecture argument
[ $# -ge 2 ] && fpga_arch="$2"
echo "[INFO] FPGA Architecture: '$fpga_arch'"

# Output directories
run_dir="${PROJECT_PATH}/run_dir/${output_name}"
output_dir="${PROJECT_PATH}/outputs"

# Run simulations
tool="${PROJECT_TOOLS_PATH}/run_softcore.py"
$tool $softcore $fpga_arch \
    $common_params \
    --run-dir $run_dir \
    --run-tests ${PROJECT_PATH}/tests/bram_partition_sweep_params.csv

# Report results
tool="${PROJECT_TOOLS_PATH}/report_yosys_vpr.py"
$tool $run_dir/run* -o $output_dir/$output_name.yosys-vpr.csv
