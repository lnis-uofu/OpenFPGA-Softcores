#!/usr/bin/env python3

import os
from utils.parsers.base_parser import BaseParser

class YosysLogParser(BaseParser):
    def __init__(self,
                 logger_filename = "yosys_output.log",
                 searchdir       = os.path.join("run_dir", "latest")):
        # inherits from the generic ReportParser class
        super().__init__(logger_filename, searchdir)
        # define parsing rules
        self.add_regex_rule(r'ABC RESULTS:\s+\$lut cells:\s+(\d+)', "abc_luts")
        self.add_regex_rule(r'ABC RESULTS:\s+internal signals:\s+(\d+)', "abc_intern_signals")
        self.add_regex_rule(r'ABC RESULTS:\s+input signals:\s+(\d+)', "abc_input_signals")
        self.add_regex_rule(r'ABC RESULTS:\s+output signals:\s+(\d+)', "abc_output_signals")
        self.add_regex_rule(r'Number of wires:\s+(\d+)', "wires")
        self.add_regex_rule(r'Number of wire bits:\s+(\d+)', "wire_bits")
        self.add_regex_rule(r'Number of public wires:\s+(\d+)', "public_wires")
        self.add_regex_rule(r'Number of public wire bits:\s+(\d+)', "public_wire_bits")
        self.add_regex_rule(r'Number of cells:\s+(\d+)', "total_cells")
        self.add_multiline_regex_rule(
            r'Number of cells:', r'^$', r'([^ ]+)\s+(\d+)', "cells")
        # parse the file
        self.parse()

