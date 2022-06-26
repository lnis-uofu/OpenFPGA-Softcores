#!/usr/bin/env python3

import os, sys
from os.path import abspath, dirname, join
from string import Template
from utils import ProjectEnv

# For configuration task file parsing
from configparser import ConfigParser
import xml.etree.ElementTree as ET

## Check if the OPENFPGA_PATH environment variable exist
if not os.environ.get('OPENFPGA_PATH', None):
    raise RuntimeError("Please source 'openfpga.sh' script in the OpenFPGA github repo first!")


class OpenfpgaTaskLauncher(ProjectEnv):
    """Generate an *OpenFPGA* task file and run it with the framework.

    Args:
        template_file (str): File name of the *OpenFPGA*-based template task.
        output_dir (str, optional): Output path name when running the task,
            usually refering to the ``run_dir``.
        device_layout (str, optional): Specify the FPGA device layout.
        channel_width (str, optional): Specify the FPGA channel width.
        abc_command (str, optional): Specify the default *ABC* executable,
            usually between (*abc* or *abc9*).
        lut_max_width (str, optional): Specify arguments of the *ABC* ``-lut``
            options to improve the LUT mapping. Read the *Yosys* documentation
            for more details, typical formats are: *<width>* or *<w1>:<w2>*.

    Attributes:
        openfpga_script_dir (str): Path location of the *OpenFPGA* scripts.
        openfpga_run_task (str): Executable of the *OpenFPGA* task file.
        target_file (str): Generated *OpenFPGA* task file name, saved in the
            *output_dir* directory.
    """

    # Q&D fix: we use a modified 'run_fpga_task.py' script to adapt the parameters
    # to pass to the Yosys, such as 'YOSYS_ABC_COMMAND' and 'YOSYS_LUT_SIZE'.
    openfpga_script_dir = abspath(join(ProjectEnv.project_path,"openfpga_flow","scripts"))
    openfpga_run_task   = abspath(join(openfpga_script_dir,"run_fpga_task.py"))

    def __init__(self, template_file, output_dir='.', **kwargs):
        # prepare the template and target files
        self.template_file  = os.path.abspath(template_file)
        self.output_dir     = os.path.abspath(output_dir)
        self.target_file    = os.path.join(self.output_dir, "config", "task.conf")
        # default arguments
        self.device_layout  = kwargs.get('device_layout', 'auto')
        self.channel_width  = kwargs.get('channel_width', 'auto')
        self.abc_command    = kwargs.get('abc_command', 'abc9')
        self.lut_max_width  = kwargs.get('lut_max_width', 'auto')
        # Read task template file
        self._parse_task_file()
        # Set up other default parameters
        if self.channel_width == "auto":
            self.channel_width = -1
        if self.lut_max_width == "auto":
            self._extract_lut_size_from_the_arch()

    def _parse_task_file(self):
        """Parse the task file to extract user variables."""
        # check if the template file exist
        if not os.path.isfile(self.template_file):
            raise OSError(f"File '{self.template_file}' not found!")
        # extract the template (to replace with user arguments)
        self.template = Template(open(self.template_file, 'r').read())

    def _extract_lut_size_from_the_arch(self):
        """
        Extract the LUT max lut size parameter from the FPFA architecture
        (XML) file.
        """
        # read the configuration task file
        config = ConfigParser(allow_no_value=True)
        config.read_file(open(self.template_file))
        # get the XML architecture
        if "ARCHITECTURES" not in config:
            raise RuntimeError("Missing 'ARCHITECTURES' section in the task file!")
        arch = config["ARCHITECTURES"]
        arch0 = arch.get('arch0', None)
        if arch0 is None:
            raise RuntimeError("Missing architecture definition 'arch0' in the task file!")
        # replace PATH:OPENFPGA_PATH, PROJECT_DIR variables
        task_vars = {
            '${PATH:OPENFPGA_PATH}': os.environ['OPENFPGA_PATH'],
            '${PROJECT_DIR}'       : self.project_path,
        }
        arch_file = arch0
        for key, val in task_vars.items():
            arch_file = arch_file.replace(key, val)
        # read the architecture file
        root = ET.parse(arch_file).getroot()
        lut_widths = [0]
        for pb_type in root.iter("pb_type"):
            if pb_type.get("class") == "lut":
                lut_widths.append(int(pb_type.find("input").get("num_pins")))
        self.lut_max_width = max(lut_widths)

    def configure_task(self, **kwargs):
        """Generate the *OpenFPGA*-based configuration task file."""
        # Define the benchmark parameters
        if not hasattr(self, "bench_files"):
            raise AttributeError("Missing 'bench_files' attribute")
        if not hasattr(self, "bench_top_module"):
            raise AttributeError("Missing 'bench_top_module' attribute")
        # Generate the OpenFPGA task configuration file
        task_vars = {
            "PROJECT_DIR"           : self.project_path,
            "BENCH_FILES"           : self.bench_files,
            "BENCH_TOP_MODULE"      : self.bench_top_module,
            "VPR_DEVICE_LAYOUT"     : self.device_layout,
            "VPR_CHANNEL_WIDTH"     : self.channel_width,
            "YOSYS_ABC_COMMAND"     : self.abc_command,
            "YOSYS_LUT_MAX_WIDTH"   : self.lut_max_width,
        }
        # Create the output directory if missing
        if not os.path.isdir(os.path.dirname(self.target_file)):
            os.makedirs(os.path.dirname(self.target_file))
        # Render the OpenFPGA task file
        with open(self.target_file, 'w') as fp:
            fp.write(self.template.safe_substitute(task_vars))

    def run(self, debug=False, **kwargs):
        """Run the *OpenFPGA* simulation with the generated task file.

        Args:
            debug (bool, optional): Enable the *debug* option in the flow.
            task_options (list, optional): Additional task flow options.
        """
        task_options = kwargs.get("task_options", [])
        if debug:
            task_options.append("--debug")
        task_options = ' '.join(task_options)
        os.system(f"python3 {self.openfpga_run_task} {self.output_dir} {task_options}")

