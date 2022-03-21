#!/usr/bin/env python3

import os
from utils.parsers.base_parser import BaseParser

class OpenfpgaTaskLogger(BaseParser):
    def __init__(self,
                 filename  = "*_out.log",
                 searchdir = os.path.join("run_dir", "latest")):
        # inherits from the generic ReportParser class
        super().__init__(filename, searchdir)
        # Define parsing rules
        self.add_regex_rule(r'ys_tmpl_yosys_vpr([^ /;]+)flow.ys ', "yosys_flow")
        # parse the file
        self.parse()

