#!/usr/bin/env python3

import os
from utils.parsers.base_parser import BaseParser


class OpenfpgaShell(BaseParser):
    def __init__(self,
                 filename  = "*_run.openfpga",
                 searchdir = os.path.join("run_dir", "latest")):
        # inherits from the generic ReportParser class
        super().__init__(filename, searchdir)
        # define parsing rules
        self.add_regex_rule(r'^vpr .+/([^/]+)\.xml', "arch")
        self.add_regex_rule(r'^vpr .+/(run\d+)/.+\.xml', "run")
        self.add_regex_rule(r'--device ([^ ]+)', "device_layout")
        self.add_regex_rule(r'--route_chan_width ([^ ]+)', "channel_width")
        # parse the file
        self.parse()

