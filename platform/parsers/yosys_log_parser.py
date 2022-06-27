#!/usr/bin/env python3

import os
from .base_parser import BaseParser

class YosysLogParser(BaseParser):
    """Parse *Yosys* ``.log`` file to extract the number of signals and cells
    used to map the design on the FPGA.

    Data extracted from the *Yosys* parser:

    - number of LUTs,
    - number of internal signals,
    - number of input signals,
    - number of output signals,
    - number of wires,
    - number of public wires,
    - number of bits per wires,
    - number of bits per public wires,
    - total number of cells,
    - detailed count per type of cells.

    Args:
        logger_filename (str, optional): File name of the file to parse.
        searchdir (str, optional): base path to recursively search for the
            logger file to parse.
    """

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

