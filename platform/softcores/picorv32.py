#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from string import Template
from utils import ProjectEnv
from parsers.base_parser import BaseParser

class PicoRV32(ProjectEnv):
    """PicoRV32 soft-core with instruction and data memory.

    Attributes:
        output_dir (str): Directory to save the generated PicoSoC top module.
        top_module (str): Top module name instance.
        top_tmpl_file (str): Top module template file.
        top_target_file (str): Top module generated file.
        source_dir (str): Third party source files.

    Args:
        output_dir (str): Directory to save the PicoSoC top module
            (default: ``.``).
        memory_size (int, optional): specify the cache memory size in Bytes
            (default: ``1024``).
        enable_fast_mul (int, optional): enable the fast multiplier in the core
            (default: ``0``).
    """

    def __init__(self, output_dir=".", **kwargs):
        # softcore parameters
        self.output_dir      = os.path.abspath(output_dir)
        self.top_module      = "picosoc"
        self.top_tmpl_file   = os.path.join(self.softcore_tmpl_path, "picosoc.v")
        self.top_target_file = os.path.join(self.output_dir, "picosoc.v")
        self.source_dir      = os.path.join(self.softcore_3rd_path, "picorv32")
        # optional parameters
        self.memory_size     = kwargs.get('memory_size', 1024)
        self.enable_fast_mul = kwargs.get('enable_fast_mul', 0)

    def _prepare_files(self, template, target):
        """Check if files/folders exists."""
        # Check if the templates exist
        if not os.path.isfile(template):
            raise OSError(f"File '{template}' not found!")
        # Create the output directory if missing
        if not os.path.isdir(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))

    def _configure_core_files(self, template_vars={}):
        """Generate the PicoSoC top module (Verilog-based)."""
        self._prepare_files(self.top_tmpl_file, self.top_target_file)
        # Render the top Verilog module
        template = Template(open(self.top_tmpl_file, 'r').read())
        with open(self.top_target_file, 'w') as fp:
            fp.write(template.safe_substitute(template_vars))
        # Generate the benchmark variables for the OpenFPGA task script
        self.core_files = ','.join([
            self.top_target_file,
            os.path.join(self.source_dir, "picosoc", "simpleuart.v"),
            os.path.join(self.source_dir, "picorv32.v"),
        ])

    def configure_rv32i(self):
        """Configure the PicoSoC with base integer instruction set."""
        self._configure_core_files({
            "enable_mul"        : 0,
            "enable_div"        : 0,
            "enable_fast_mul"   : 0,
            "enable_compressed" : 0,
            "memory_size"       : int(self.memory_size/4),
        })

    def configure_rv32im(self):
        """Configure the PicoSoC with multiplier/divider support."""
        self._configure_core_files({
            "enable_mul"        : 1,
            "enable_div"        : 1,
            "enable_fast_mul"   : self.enable_fast_mul,
            "enable_compressed" : 0,
            "memory_size"       : int(self.memory_size/4),
        })

    def configure_rv32imc(self):
        """Configure the PicoSoC with multiplier/divider and compressed
        instruction support.
        """
        self._configure_core_files({
            "enable_mul"        : 1,
            "enable_div"        : 1,
            "enable_fast_mul"   : self.enable_fast_mul,
            "enable_compressed" : 1,
            "memory_size"       : int(self.memory_size/4),
        })


class PicosocParser(BaseParser):
    """
    Define a report parser to catch the memory size post-simulation, looking
    inside the result directory ``run_dir/``.
    This object inherits from the default ``BaseParser`` class, which provides
    basic method to set up the regex for parsing.

    Args:
        filename (str): Name of the file to parse (default: ``picosoc.v``).
        searchdir (str): Base path to search the file (default:
            ``run_dir/latest``).
    """
    def __init__(self,
                 filename  = "picosoc.v",
                 searchdir = os.path.join("run_dir", "latest")):
        # inherits from the generic ReportParser class
        super().__init__(filename, searchdir)
        # define parsing rules
        self.add_regex_rule(r'parameter integer MEM_WORDS\s*=\s*(\d+)\s*;', "memory_size")

    def parse(self):
        """Parse the top Verilog module file of the soft-core."""
        # call the parent method
        super().parse()
        # fix the caught memory size, which is multiply by 4
        if "memory_size" in self.results:
            self.results["memory_size"] = int(self.results['memory_size'])*4
