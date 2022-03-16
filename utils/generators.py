#!/usr/bin/env python3

import os, sys, re
from utils.project import ProjectEnv

class Template(object):
    """
    Class used to generate 'target_file' using template file structures.
    """
    def __init__(self, template_file, output_dir='.', debug=False):
        self.template_file = os.path.abspath(template_file)
        self.output_dir    = os.path.abspath(output_dir)

    def render(self, target_filename, template_vars={}):
        """
        Generate a target file according to a double accolades formatted
        template file. Each variable is contained into a dictionary.
        """
        # Read the full template contents
        with open(self.template_file, 'r') as fp:
            template = fp.read()
        # Replace all double accolades structures
        for key, value in template_vars.items():
            template = re.sub(f'{{{{\s*{key}\s*}}}}', f"{value}", template)
        # Create the basedir if it's not existing
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)
        # write the task file with the right variables
        with open(os.path.join(self.output_dir, target_filename), "w") as fp:
            fp.write(template)


class Task(Template,ProjectEnv):
    """
    Class used to generate OpenFPGA task (.conf) launchers.
    """
    def __init__(self, template_task_file, output_dir='.', **kwargs):
        super().__init__(template_task_file, output_dir)
        # default arguments
        self.device_layout = kwargs.get('device_layout', 'auto')
        self.channel_width = kwargs.get('channel_width', 'auto')

    def configure_task(self, **kwargs):
        """
        Generate the OpenFPGA configuration task.
        """
        # Define the benchmark parameters
        if not hasattr(self, "bench_files"):
            raise AttributeError("Missing 'bench_files' attribute")
        if not hasattr(self, "bench_top_module"):
            raise AttributeError("Missing 'bench_top_module' attribute")
        # Default value of the channel width constraint
        if self.channel_width == "auto":
            chan_width = -1
        else:
            chan_width = self.channel_width
        # Generate the OpenFPGA task configuration file
        task_vars = {
            "openfpga_shell_tmpl"           : self.openfpga_shell_flow,
            "vpr_route_chan_width"          : chan_width,
            "vpr_device_layout"             : self.device_layout,
            "bench_files"                   : self.bench_files,
            "bench_top_module"              : self.bench_top_module,
            # FIXME: this a patch waiting for the PR of the corrected BRAM flow
            "yosys_vpr_bram_flow_tmpl"      : self.yosys_bram_flow,
            "yosys_vpr_bram_dsp_flow_tmpl"  : self.yosys_bram_dsp_flow,
        }
        # Render the OpenFPGA task file
        self.render(os.path.join(self.output_dir, "config", "task.conf"), task_vars)

    def run(self, debug=False, **kwargs):
        """
        Run the OpenFPGA task architecture simulation.
        """
        task_options = kwargs.get("task_options", [])
        if debug:
            task_options.append("--debug")
        os.system(f"python3 {self.run_fpga_task} {self.output_dir} {' '.join(task_options)}")

