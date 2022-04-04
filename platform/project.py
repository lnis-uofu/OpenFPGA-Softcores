#!/usr/bin/env python3

import os
from os.path import abspath, dirname, join

## Check if the OPENFPGA_PATH environment variable exist
if not os.environ.get('OPENFPGA_PATH', None):
    raise RuntimeError("Please source 'openfpga.sh' script in the OpenFPGA github repo first!")

class ProjectEnv:
    """
    Base directories, paths and files variables for this project, to facilitate
    absolute file manipulation.
    """

    # Project dirs
    utils_dir           = abspath(dirname(__file__))
    project_dir         = abspath(join(utils_dir, ".."))
    softcore_dir        = abspath(join(project_dir, "softcores"))
    softcore_tmpl_dir   = abspath(join(softcore_dir, "templates"))
    third_party_dir     = abspath(join(project_dir, "third_party"))

    # OpenFPGA framework
    openfpga_path       = os.environ['OPENFPGA_PATH']
    openfpga_script_dir = abspath(join(openfpga_path, "openfpga_flow", "scripts"))
    run_fpga_task       = abspath(join(openfpga_script_dir, "run_fpga_task.py"))

