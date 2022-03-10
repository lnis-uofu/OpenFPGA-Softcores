#!/usr/bin/env python3

"""
Just another Python generator of OpenFPGA tasks to evaluate softcore performances.
"""

import os
import argparse
from glob import glob
from softcores import *

# Check if the OPENFPGA_PATH environment variable exist
if not os.environ.get('OPENFPGA_PATH', None):
    raise RuntimeError("Please source 'openfpga.sh' script in the OpenFPGA github repo first!")

# List of available soft-cores to evaluate
available_softcores = glob("softcores/[!_]*.py")
available_softcores = [os.path.basename(s)[:-3] for s in available_softcores]
available_softcores.remove("utils")
available_softcores.remove("parsers")

# List of available RISC-V ISA extensions
available_riscv_isa = ['i','im','imc']

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description     = __doc__,
        formatter_class = argparse.RawTextHelpFormatter
    )
    # positional arguments
    ap.add_argument('softcore',
                    help="Soft-core processor to evaluate",
                    choices=available_softcores)
    ap.add_argument('task_file', metavar="<fpga-arch-file>",
                    help="FPGA architecture to evaluate, using any files in the 'fpga_archs/' dir")
    # optional arguments
    ap.add_argument('-d', '--debug', action='store_true', dest='debug',
                    help="Enable debug mode",
                    default=False)
    ap.add_argument('--run-dir', metavar='<path>', dest='run_dir',
                    help="Define the result directory to parse (default: %(default)s)",
                    default="run_dir")
    ap.add_argument("--device-layout", metavar="<WxH>", dest='device_layout',
                    help="Define a fixed FPGA layout (default: %(default)s)",
                    default="auto")
    ap.add_argument("--channel-width", metavar="<integer>", dest='channel_width',
                    help="Define a fixed FPGA channel width (default: %(default)s)",
                    default="auto")
    ap.add_argument("--memory-size", metavar="<integer>", dest='memory_size',
                    help="Define the memory size of the softcore (default: %(default)s)",
                    default=1024)
    ap.add_argument("--isa",
                    help="Enable RISC-V ISA extensions (default: %(default)s)",
                    choices=available_riscv_isa,
                    default="i")
    # parse the user arguments
    args = ap.parse_args()

    # Create the OpenFPGA task launcher
    task = Task(
        template_task_file  = args.task_file,
        output_dir          = args.run_dir,
        device_layout       = args.device_layout,
        channel_width       = args.channel_width,
    )

    # PicoRV32
    if args.softcore == "picorv32":
        core = PicoRV32(
            output_dir      = args.run_dir,
            memory_size     = int(args.memory_size),
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

