#!/usr/bin/env python3

import os
from os.path import abspath, dirname, join


class ProjectEnv:
    """
    Base directories, paths and files variables for this project, to facilitate
    absolute file manipulation.
    """

    # Project dirs
    utils_dir           = abspath(dirname(__file__))
    project_dir         = abspath(join(utils_dir, ".."))

    # OpenFPGA templates
    openfpga_dir        = abspath(join(project_dir, "openfpga_flow"))
    openfpga_shell_dir  = abspath(join(openfpga_dir, "openfpga_shell_scripts"))
    openfpga_shell_flow = abspath(join(openfpga_shell_dir, "arch_exploration_only_vpr.openfpga"))

    # Yosys templates
    yosys_flow_dir      = abspath(join(openfpga_dir, "misc"))
    yosys_bram_flow     = abspath(join(yosys_flow_dir, "ys_tmpl_yosys_vpr_bram_flow.ys"))
    yosys_bram_dsp_flow = abspath(join(yosys_flow_dir, "ys_tmpl_yosys_vpr_bram_dsp_flow.ys"))

    # OpenFPGA framework
    openfpga_path       = os.environ.get('OPENFPGA_PATH', None)
    if openfpga_path is None:
        raise RuntimeError("Missing 'OPENFPGA_PATH' environment variable!")
    openfpga_script_dir = abspath(join(openfpga_path, "openfpga_flow", "scripts"))
    run_fpga_task       = abspath(join(openfpga_script_dir, "run_fpga_task.py"))

