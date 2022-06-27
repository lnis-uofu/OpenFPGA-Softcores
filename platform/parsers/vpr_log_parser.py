#!/usr/bin/env python3

import os
from .base_parser import BaseParser

class VprLogParser(object):
    """Parse *VPR* ``.log`` and ``.result`` files to extract place and routing
    information when the design is mapped on the FPGA.

    Data extracted from the *VPR* parser:

    - *Physical Block* (PB) types and their occupation ratio,
    - device grid dimensions,
    - device (best) channel width,
    - maximum design frequency,
    - critical path of the design,
    - average net length,
    - average bends per net,
    - average wire segment per net,
    - maximum segments used by a net,
    - total routing area,
    - total logic block area,
    - total wire length.

    Args:
        stats_filename (str, optional): File name of the result file to parse.
        logger_filename (str, optional): File name of the logger file to parse.
        searchdir (str, optional): base path to recursively search for the
            logger file to parse.
    """

    def __init__(self,
                 stats_filename  = "vpr_stat.result",
                 logger_filename = "vpr_stdout.log",
                 searchdir       = os.path.join("run_dir","latest")):
        # Logger file
        self.logger = BaseParser(logger_filename, searchdir, "vpr_logger")
        self._define_logger_parsing_rules()
        self.logger.parse()
        # Result file
        self.stats = BaseParser(stats_filename, searchdir, "vpr_stats")
        self._define_stats_parsing_rules()
        self.stats.parse()

    def __str__(self):
        return f"{self.logger}\n{self.stats}"

    def _define_logger_parsing_rules(self):
        self.logger.add_multiline_regex_rule(
            r'^Pb types usage', r'^$', r'\s+([^ :]+)\s*:\s+(\d+)', "pb_types")
        self.logger.add_regex_rule(r'^FPGA sized to (\d+ x \d+):', "device_layout")
        self.logger.add_regex_rule(r'Fmax:\s+(.+)', "max_frequency")
        self.logger.add_regex_rule(r'Maximum net length:\s+(\d+)', "max_net_length")
        self.logger.add_regex_rule(r'^Average number of bends per net:\s+([^ ]+)', "avg_bends_per_net")
        self.logger.add_regex_rule(r'Maximum \# of bends:\s+(\d+)', "max_bends")
        self.logger.add_regex_rule(r'average wire segments per net:\s+([^ ]+)', "avg_segments_per_net")
        self.logger.add_regex_rule(r'Maximum segments used by a net:\s+(\d+)', "max_segments_per_net")
        # Channel width
        self.logger.add_regex_rule(r'^Best routing .+ (\d+)\.', "channel_width")
        self.logger.add_regex_rule(r'^Circuit successfully routed .+ (\d+)\.', "channel_width")
        self.logger.add_regex_rule(r'^Circuit is (unroutable)', "channel_width")

    def _define_stats_parsing_rules(self):
        self.stats.add_regex_rule(r'^clb_blocks = (\d+)', "clb_blocks")
        self.stats.add_regex_rule(r'^io_blocks = (\d+)', "io_blocks")
        self.stats.add_regex_rule(r'^memory_blocks = (\d+)', "memory_blocks")
        self.stats.add_regex_rule(r'^average_net_length = ([^ ]+)', "avg_net_length")
        self.stats.add_regex_rule(r'^critical_path = ([^ ]+)', "critical_path")
        self.stats.add_regex_rule(r'^total_routing_area = ([^ ]+)', "total_routing_area")
        self.stats.add_regex_rule(r'^total_logic_block_area = ([^ ]+)', "total_logic_block_area")
        self.stats.add_regex_rule(r'^total_wire_length = ([^ ]+)', "total_wire_length")

