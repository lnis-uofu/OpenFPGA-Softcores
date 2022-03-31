#!/usr/bin/env python3

import os, sys, re
from string import Template
from utils.project import ProjectEnv


class OpenfpgaTaskLauncher(ProjectEnv):
    """
    Class used to generate OpenFPGA task (.conf) launchers.
    """
    def __init__(self, template_file, output_dir='.', **kwargs):
        # prepare the template and target files
        self.template_file  = os.path.abspath(template_file)
        self.output_dir     = os.path.abspath(output_dir)
        self.target_file    = os.path.join(self.output_dir, "config", "task.conf")
        # default arguments
        self.device_layout  = kwargs.get('device_layout', 'auto')
        self.channel_width  = kwargs.get('channel_width', 'auto')

    def configure_task(self, **kwargs):
        """
        Generate the OpenFPGA configuration task.
        """
        # check if the template file exist
        if not os.path.isfile(self.template_file):
            raise OSError(f"File '{self.template_file}' not found!")
        self.template = Template(open(self.template_file, 'r').read())
        # Define the benchmark parameters
        if not hasattr(self, "bench_files"):
            raise AttributeError("Missing 'bench_files' attribute")
        if not hasattr(self, "bench_top_module"):
            raise AttributeError("Missing 'bench_top_module' attribute")
        # Default value of the channel width constraint
        if self.channel_width == "auto":
            channel_width = -1
        else:
            channel_width = self.channel_width
        # Generate the OpenFPGA task configuration file
        task_vars = {
            "PROJECT_DIR"           : self.project_dir,
            "BENCH_FILES"           : self.bench_files,
            "BENCH_TOP_MODULE"      : self.bench_top_module,
            "VPR_DEVICE_LAYOUT"     : self.device_layout,
            "VPR_CHANNEL_WIDTH"     : channel_width,
        }
        # Create the output directory if missing
        if not os.path.isdir(os.path.dirname(self.target_file)):
            os.makedirs(os.path.dirname(self.target_file))
        # Render the OpenFPGA task file
        with open(self.target_file, 'w') as fp:
            fp.write(self.template.safe_substitute(task_vars))

    def run(self, debug=False, **kwargs):
        """
        Run the OpenFPGA task architecture simulation.
        """
        task_options = kwargs.get("task_options", [])
        if debug:
            task_options.append("--debug")
        task_options = ' '.join(task_options)
        os.system(f"python3 {self.run_fpga_task} {self.output_dir} {task_options}")

