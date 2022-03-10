#!/usr/bin/env python3

import os, sys, re
from glob import glob
from collections import OrderedDict

class ReportParser(object):
    """
    Class used to parse any loggers, reports or results file, mostly using
    regular expression and tokens.
    """
    def __init__(self, filename, **kwargs):
        # if basedir is defined, automatically locate the file path
        basedir = kwargs.get('basedir', None)
        if basedir is not None:
            filenames = glob(f"{basedir}/**/{filename}", recursive=True)
            if len(filenames) != 1:
                print(f"Warning: '{filename}' not found in '{basedir}'!")
            else:
                filename = filenames[0]
        # save the full filename path
        self.filename       = filename
        # save all parsed results in a dictionary
        self.results        = OrderedDict()
        # keep each regex rules in a dictionary
        self._regex_rules   = []
        self._mregex_rules  = []

    def __str__(self):
        return '\n'.join([f"{k} = {v}" for k, v in self.results.items()])

    def add_regex_rule(self, regex, keyname):
        self._regex_rules.append({
                'key'   : keyname,
                'regex' : regex,
        })

    def add_multiline_regex_rule(self, start_trig, end_trig, regex, keyname):
        self._mregex_rules.append({
                'key'   : keyname,
                'start' : start_trig,
                'end'   : end_trig,
                'regex' : regex,
                'token' : False,
        })

    def parse(self):
        # test if the file exist
        if not os.path.isfile(self.filename):
            print(f"Warning: '{self.filename}' not found!")
            return
        # parse the file
        with open(self.filename, 'r') as fp:
            for line in fp.readlines():
                line = line.rstrip()
                # single line regex parsing
                for rule in self._regex_rules:
                    m = re.search(rule['regex'], line)
                    if m:
                        self.results[rule['key']] = m.group(1)
                # multiline regex parsing
                for rule in self._mregex_rules:
                    # end trigger
                    if rule['token'] is True and re.search(rule['end'],line):
                        rule['token'] = False
                    # catch the multiline contents
                    m = re.search(rule['regex'], line)
                    if m and rule['token']:
                        self.results[f"{rule['key']}.{m.group(1)}"] = m.group(2)
                    # start trigger
                    if rule['token'] is False and re.search(rule['start'],line):
                        rule['token'] = True

class YosysReport(ReportParser):

    def __init__(self,
                 logger_filename = "yosys_output.log",
                 **kwargs):
        # set the base directory to look up
        self.basedir = kwargs.get("basedir", os.path.join("run_dir","latest"))
        super().__init__(logger_filename, basedir=self.basedir)
        # Define parsing rules
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

    def __str__(self):
        return "[YOSYS_LOGGER]\n" + super().__str__()

class VprReport(object):

    def __init__(self,
                 result_filename = "vpr_stat.result",
                 logger_filename = "vpr_stdout.log",
                 **kwargs):
        # set the base directory to look up
        self.basedir = kwargs.get("basedir", os.path.join("run_dir","latest"))
        # Logger file
        self._logger = ReportParser(logger_filename, basedir=self.basedir)
        self._define_logger_parsing_rules()
        self._logger.parse()
        # Result file
        self._result = ReportParser(result_filename, basedir=self.basedir)
        self._define_result_parsing_rules()
        self._result.parse()

    def __str__(self):
        return "[VPR_LOGGER]\n" + str(self._logger) + "\n[VPR_RESULTS]\n" + str(self._result)

    def _define_logger_parsing_rules(self):
        self._logger.add_multiline_regex_rule(
            r'Blocks: \d+', r'Nets\s*: \d+', r'([^ ]+)\s*:\s*(\d+)', "circuit_blocks")
        self._logger.add_regex_rule(r'^FPGA sized to (\d+ x \d+):', "device_layout")
        self._logger.add_regex_rule(r'Fmax:\s+(.+)', "max_frequency")
        # Channel width
        self._logger.add_regex_rule(r'^Best routing .+ (\d+)\.', "channel_width")
        self._logger.add_regex_rule(r'^Circuit successfully routed .+ (\d+)\.', "channel_width")
        self._logger.add_regex_rule(r'^Circuit is (unroutable)', "channel_width")

    def _define_result_parsing_rules(self):
        self._result.add_regex_rule(r'^clb_blocks = (\d+)', "clb_blocks")
        self._result.add_regex_rule(r'^io_blocks = (\d+)', "io_blocks")
        self._result.add_regex_rule(r'^memory_blocks = (\d+)', "memory_blocks")
        self._result.add_regex_rule(r'^average_net_length = ([^ ]+)', "average_net_length")
        self._result.add_regex_rule(r'^critical_path = ([^ ]+)', "critical_path")
        self._result.add_regex_rule(r'^total_routing_area = ([^ ]+)', "total_routing_area")
        self._result.add_regex_rule(r'^total_logic_block_area = ([^ ]+)', "total_logic_block_area")
        self._result.add_regex_rule(r'^total_wire_length = ([^ ]+)', "total_wire_length")

class OpenfpgaShell(ReportParser):
    def __init__(self, filename = "*_run.openfpga", **kwargs):
        # set the base directory to look up
        self.basedir = kwargs.get("basedir", os.path.join("run_dir","latest"))
        super().__init__(filename, basedir=self.basedir)
        # Define parsing rules
        self.add_regex_rule(r'^vpr .+/([^/]+)\.xml', "arch")
        self.add_regex_rule(r'^vpr .+/(run\d+)/.+\.xml', "run")
        self.add_regex_rule(r'--device ([^ ]+)', "device_layout")
        self.add_regex_rule(r'--route_chan_width ([^ ]+)', "channel_width")
        # parse the file
        self.parse()

    def __str__(self):
        return "[SIM_PARAMS]\n" + super().__str__()

class TaskLogger(ReportParser):
    def __init__(self, filename = "*_out.log", **kwargs):
        # set the base directory to look up
        self.basedir = kwargs.get("basedir", os.path.join("run_dir","latest"))
        super().__init__(filename, basedir=self.basedir)
        # Define parsing rules
        self.add_regex_rule(r'ys_tmpl_yosys_vpr([^ /;]+)flow.ys ', "yosys_flow")
        # parse the file
        self.parse()

class PicosocReport(ReportParser):
    def __init__(self, filename="picosoc.v", **kwargs):
        # set the base directory to look up
        self.basedir = kwargs.get("basedir", os.path.join("run_dir","latest"))
        super().__init__(filename, basedir=self.basedir)
        # Define parsing rules
        self.add_regex_rule(r'parameter integer MEM_WORDS\s*=\s*(\d+)\s*;', "memory_size")
        # parse the file
        self.parse()
