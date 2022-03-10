#!/usr/bin/env python3

import os
from softcores.utils import Template

class PicoRV32(Template):

    def __init__(self, output_dir=".", **kwargs):
        super().__init__(
            os.path.abspath('benchmarks/picosoc.v'),
            output_dir,
        )
        self.top_module      = "picosoc"
        self.target_filename = "picosoc.v"
        self.root_dir        = os.path.abspath('third_party/picorv32')
        self.target_file     = os.path.abspath(os.path.join(self.output_dir, self.target_filename))
        # optional parameters
        self.memory_size     = kwargs.get('memory_size', 1024)
        self.enable_fast_mul = kwargs.get('enable_fast_mul', 0)

    def configure_core_files(self, core_template_vars={}):
        """
        Generate the PicoSoC top module (Verilog-based)
        """
        # Render the top Verilog module
        self.render(self.target_file, core_template_vars)
        # Generate the benchmark variables for the OpenFPGA task script
        self.core_files = ','.join([
            self.target_file,
            f"{self.root_dir}/picosoc/simpleuart.v",
            f"{self.root_dir}/picorv32.v",
        ])

    def configure_rv32i(self):
        self.configure_core_files({
            "enable_mul"        : 0,
            "enable_div"        : 0,
            "enable_fast_mul"   : 0,
            "enable_compressed" : 0,
            "memory_size"       : int(self.memory_size/4),
        })

    def configure_rv32im(self):
        self.configure_core_files({
            "enable_mul"        : 1,
            "enable_div"        : 1,
            "enable_fast_mul"   : self.enable_fast_mul,
            "enable_compressed" : 0,
            "memory_size"       : int(self.memory_size/4),
        })

    def configure_rv32imc(self):
        self.configure_core_files({
            "enable_mul"        : 1,
            "enable_div"        : 1,
            "enable_fast_mul"   : self.enable_fast_mul,
            "enable_compressed" : 1,
            "memory_size"       : int(self.memory_size/4),
        })

