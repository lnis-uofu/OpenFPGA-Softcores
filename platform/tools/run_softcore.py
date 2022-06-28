#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Just another Python generator of OpenFPGA tasks to evaluate softcore performances.
"""

import os
import sys
import csv
import argparse
from glob import glob

# 'tools/' is a sibling folders of 'parsers/', the following command ensures
# the import of libraries from the sibling folder.
sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, ".."))))

from utils import ProjectEnv
from softcores import *
from generators.openfpga_task_gen import OpenfpgaTaskLauncher

## Check if the OPENFPGA_PATH environment variable exist
if not os.environ.get('OPENFPGA_PATH', None):
    raise RuntimeError("Please source 'openfpga.sh' script in the OpenFPGA github repo first!")

## List of available soft-cores to evaluate
project             = ProjectEnv()
available_softcores = glob(f"{project.softcore_path}/[!_]*.py")
available_softcores = [os.path.basename(s)[:-3] for s in available_softcores]

# ============================================================================
#  Command-line arguments
# ============================================================================

ap = argparse.ArgumentParser(
    description     = __doc__,
    formatter_class = argparse.RawTextHelpFormatter
)
# Positional arguments
ap.add_argument(
    'softcore',
    choices = available_softcores,
    help    = "Soft-core processor to evaluate",
)
ap.add_argument(
    'fpga_arch',
    metavar = "<fpga-arch-file>",
    help    = "FPGA architecture to evaluate, using any files in the 'fpga_archs/' dir",
)
# Optional arguments
ap.add_argument(
    '-d', '--debug',
    action  = "store_true",
    default = False,
    help    = "Enable debug mode (default: %(default)s)",
)
# Architecture-related arguments
ap.add_argument(
    '--device-layout',
    metavar = "<width>x<height>|auto",
    default = "auto",
    help    = "Define a fixed FPGA layout dimensions (default: %(default)s)",
)
ap.add_argument(
    '--channel-width',
    metavar = "<int>|auto",
    default = "auto",
    help    = "Define a fixed FPGA channel width (default: %(default)s)",
)
# Softcore-related arguments
ap.add_argument(
    "--cache-size",
    metavar = "<int>",
    type    = int,
    default = 1024,
    help    = "Define the memory size (L1) of the core in bytes (default: %(default)s)",
)
ap.add_argument(
    "--isa",
    choices = ['i','im','imc'],
    default = "i",
    help    = "Enable RISC-V ISA extensions (default: %(default)s)",
)
# Synthesis-related arguments
ap.add_argument(
    "--abc-command",
    choices = ["abc", "abc9"],
    default = "abc9",
    help    = "ABC executable used to evaluate different mapping strategies (default: %(default)s)",
)
ap.add_argument(
    "--lut-max-width",
    metavar = "<width>|<w1>:<w2>|auto",
    default = "auto",
    help    = "ABC LUT mapping using a specified (max) LUT width (default: %(default)s)",
)
# Design space exploration simulations
ap.add_argument(
    "--run-tests",
    metavar = "<csv-file>",
    help    = "Run multiple simulations listed in CSV file, giving all arguments by columns",
)
ap.add_argument(
    '--run-dir',
    metavar = "<path>",
    default = "run_dir",
    help    = "Save all OpenFPGA outputs in a given directory (default: %(default)s)",
)
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
        abc_command     = args.abc_command,
        lut_max_width   = args.lut_max_width,
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
    with open(args.run_tests, 'r') as fp:
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
    if args.run_tests:
        run_multiple_tasks()
    else:
        run_single_task()
