#!/usr/bin/env python3

"""
Just another Python generator of OpenFPGA tasks to evaluate softcore performances.
"""

import os, csv, argparse
from glob import glob
from softcores import *
from utils.generators.openfpga_task_gen import OpenfpgaTaskLauncher

## Check if the OPENFPGA_PATH environment variable exist
if not os.environ.get('OPENFPGA_PATH', None):
    raise RuntimeError("Please source 'openfpga.sh' script in the OpenFPGA github repo first!")

## List of available soft-cores to evaluate
available_softcores = glob("softcores/[!_]*.py")
available_softcores = [os.path.basename(s)[:-3] for s in available_softcores]

## List of available RISC-V ISA extensions
available_riscv_isa = ['i','im','imc']

# ============================================================================
#  Command-line arguments
# ============================================================================

ap = argparse.ArgumentParser(
    description     = __doc__,
    formatter_class = argparse.RawTextHelpFormatter
)
# Positional arguments
ap.add_argument('softcore',
                help="Soft-core processor to evaluate",
                choices=available_softcores)
ap.add_argument('fpga_arch', metavar="<fpga-arch-file>",
                help="FPGA architecture to evaluate, using any files in the 'fpga_archs/' dir")
# Optional arguments
ap.add_argument('-d', '--debug', action="store_true", dest="debug",
                help="Enable debug mode",
                default=False)
ap.add_argument('--run-dir', metavar="<path>", dest="run_dir",
                help="Define the result directory to parse (default: %(default)s)",
                default="run_dir")
# Architecture-related arguments
ap.add_argument('--device-layout', metavar="<WxH>", dest="device_layout",
                help="Define a fixed FPGA layout (default: %(default)s)",
                default="auto")
ap.add_argument('--channel-width', metavar="<size>", dest="channel_width",
                help="Define a fixed FPGA channel width (default: %(default)s)",
                default="auto")
# Softcore-related arguments
ap.add_argument("--cache-size", metavar="<integer>", dest="cache_size",
                help="Define the memory size of the softcore (default: %(default)s)",
                default=1024)
ap.add_argument("--isa",
                help="Enable RISC-V ISA extensions (default: %(default)s)",
                choices=available_riscv_isa,
                default="i")
# Design space exploration simulations
ap.add_argument("--run-list", metavar="<csv-file>", dest="run_list",
                help="Run multiple simulations listed in CSV file, giving all arguments by columns")
# Parse the user arguments
args = ap.parse_args()

# ============================================================================
#  Functions
# ============================================================================

def run_single_task():
    """
    Single task launcher
    """
    # Create the OpenFPGA task launcher
    task = OpenfpgaTaskLauncher(
        template_file   = args.fpga_arch,
        output_dir      = args.run_dir,
        device_layout   = args.device_layout,
        channel_width   = args.channel_width,
    )
    # PicoRV32
    if args.softcore == "picorv32":
        core = PicoRV32(
            output_dir      = args.run_dir,
            memory_size     = int(args.cache_size),
            enable_fast_mul = 1,
        )
        if args.isa == "i":
            core.configure_rv32i()
        if args.isa == "im":
            core.configure_rv32im()
        if args.isa == "imc":
            core.configure_rv32imc()
        task.bench_files      = core.core_files
        task.bench_top_module = core.top_module
        task.configure_task()
        task.run()

def run_multiple_tasks():
    """
    Multiple task launcher
    """
    with open(args.run_list, 'r') as fp:
        tasks = list(csv.DictReader(fp))
        total = len(tasks)
        for idx, task in enumerate(tasks):
            arglist = ', '.join([f"{k}={v}" for k, v in task.items()])
            print(f"[task {idx+1}/{total}] args: {arglist}")
            # reset the arguments parameters
            for argname, argval in task.items():
                setattr(args, argname, argval)
            # launch the task
            run_single_task()


if __name__ == "__main__":
    if args.run_list:
        run_multiple_tasks()
    else:
        run_single_task()
