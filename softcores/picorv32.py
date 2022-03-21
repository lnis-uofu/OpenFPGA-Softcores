#!/usr/bin/env python3

import os
from string import Template
from utils.project import ProjectEnv
from utils.parsers.base_parser import BaseParser

class PicoRV32(ProjectEnv):

    def __init__(self, output_dir=".", **kwargs):
        # softcore parameters
        self.output_dir      = os.path.abspath(output_dir)
        self.top_module      = "picosoc"
        self.template_file   = os.path.join(self.softcore_tmpl_dir, "picosoc.v")
        self.source_dir      = os.path.join(self.third_party_dir, "picorv32")
        self.target_file     = os.path.join(self.output_dir, "picosoc.v")
        # optional parameters
        self.memory_size     = kwargs.get('memory_size', 1024)
        self.enable_fast_mul = kwargs.get('enable_fast_mul', 0)

    def _configure_core_files(self, template_vars={}):
        """
        Generate the PicoSoC top module (Verilog-based)
        """
        # Check if the template exist
        if not os.path.isfile(self.template_file):
            raise OSError(f"File '{self.template_file}' not found!")
        self.template = Template(open(self.template_file, 'r').read())
        # Render the top Verilog module
        with open(self.target_file, 'w') as fp:
            fp.write(self.template.safe_substitute(template_vars))
        # Generate the benchmark variables for the OpenFPGA task script
        self.core_files = ','.join([
            self.target_file,
            f"{self.source_dir}/picosoc/simpleuart.v",
            f"{self.source_dir}/picorv32.v",
        ])

    def configure_rv32i(self):
        self._configure_core_files({
            "enable_mul"        : 0,
            "enable_div"        : 0,
            "enable_fast_mul"   : 0,
            "enable_compressed" : 0,
            "memory_size"       : int(self.memory_size/4),
        })

    def configure_rv32im(self):
        self._configure_core_files({
            "enable_mul"        : 1,
            "enable_div"        : 1,
            "enable_fast_mul"   : self.enable_fast_mul,
            "enable_compressed" : 0,
            "memory_size"       : int(self.memory_size/4),
        })

    def configure_rv32imc(self):
        self._configure_core_files({
            "enable_mul"        : 1,
            "enable_div"        : 1,
            "enable_fast_mul"   : self.enable_fast_mul,
            "enable_compressed" : 1,
            "memory_size"       : int(self.memory_size/4),
        })


class PicosocReport(BaseParser):
    """
    Define a report parser to catch the memory size post-simulation, looking
    inside the result directory (run_dir).
    """
    def __init__(self,
                 filename  = "picosoc.v",
                 searchdir = os.path.join("run_dir", "latest")):
        # inherits from the generic ReportParser class
        super().__init__(filename, searchdir)
        # define parsing rules
        self.add_regex_rule(r'parameter integer MEM_WORDS\s*=\s*(\d+)\s*;', "memory_size")

    def parse(self):
        # call the parent method
        super().parse()
        # fix the caught memory size, which is multiply by 4
        if "memory_size" in self.results:
            self.results["memory_size"] = int(self.results['memory_size'])*4
