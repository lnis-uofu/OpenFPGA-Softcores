#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Just another Python report parser of Yosys and VPR results and reports.
"""

import os
import sys
import csv
import argparse
from glob import glob

# 'tools/' is a sibling folders of 'parsers/', the following command ensures
# the import of libraries from the sibling folder.
sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, ".."))))

from softcores import *
from parsers import *

# ============================================================================
#  Command-line arguments
# ============================================================================
ap = argparse.ArgumentParser(
    description     = __doc__,
    formatter_class = argparse.RawTextHelpFormatter
)
# positional arguments
ap.add_argument(
    'search_path',
    nargs   = '*',
    metavar = '<search-path>',
    default = os.path.join("run_dir", "latest"),
    help    = "Specify a base directory to search reports (default: '%(default)s')",
)
# optional arguments
ap.add_argument(
    '-d', '--debug',
    action  = 'store_true',
    help    = "Enable debug mode",
)
ap.add_argument(
    '-o', '--output',
    metavar = "<csv-file>",
    default = os.path.join("outputs", "report_parser.csv"),
    help    = "Save in CSV format (default: %(default)s)",
)
# parse the user arguments
args = ap.parse_args()

# ============================================================================
#  Classes & Functions
# ============================================================================

class CSVFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.content  = []
        self.headers  = []

    def add_headers(self, headers=[], prefix=""):
        new_headers = [f"{prefix}.{h}" for h in headers]
        self.headers = list(set(new_headers + self.headers))

    def save(self):
        with open(self.filename, 'w') as fp:
            wr = csv.DictWriter(fp, sorted(self.headers))
            wr.writeheader()
            wr.writerows(self.content)

def parse_rundir(dir_name, csv_file=None):
    """
    Parse the different report, results files
    """
    # create a new line of the csv file
    if args.output:
        csv_row = {}
    # Yosys logger (yosys_output.log)
    rpt = YosysLogParser(searchdir=dir_name)
    if args.debug:
        print(rpt)
    if args.output:
        csv_file.add_headers(rpt.results.keys(), "yosys")
        csv_row.update({f"yosys.{k}": v for k, v in rpt.results.items()})
    # Note: abort parsing if there is no yosys results
    if len(rpt.results) == 0:
        print("[-] missing Yosys results, parsing avoided")
        return
    # VPR logger and stats (vpr_stdout.log, vpr_stat.result)
    rpt = VprLogParser(searchdir=dir_name)
    if args.debug:
        print(rpt)
    if args.output:
        csv_file.add_headers(rpt.logger.results.keys(), "vpr")
        csv_file.add_headers(rpt.stats.results.keys(), "vpr")
        csv_row.update({f"vpr.{k}": v for k, v in rpt.logger.results.items()})
        csv_row.update({f"vpr.{k}": v for k, v in rpt.stats.results.items()})
    # OpenFPGA shell (VPR) parameters (*_run.openfpga)
    params = OpenfpgaShellParser(searchdir=dir_name)
    if args.debug:
        print(params)
    if args.output:
        csv_file.add_headers(params.results.keys(), "params")
        csv_row.update({f"params.{k}": v for k, v in params.results.items()})
    # OpenFPGA task logger (*_out.log) => yosys_flow
    params = OpenfpgaTaskLogParser(searchdir=dir_name)
    if args.debug:
        print(params)
    if args.output:
        csv_file.add_headers(params.results.keys(), "params")
        csv_row.update({f"params.{k}": v for k, v in params.results.items()})
    # Specific soft-core parsing section
    # Note: enable only if the file exist
    core = PicosocParser(searchdir=dir_name)
    if os.path.isfile(core.filename):
        core.parse()
        if args.debug:
            print(core)
        if args.output:
            csv_file.add_headers(core.results.keys(), "params")
            csv_row.update({f"params.{k}": v for k, v in core.results.items()})
    # add a new csv line
    if args.output:
        csv_file.content.append(csv_row)
    print(f"[+] '{dir_name}' content parsed!")


if __name__ == "__main__":
    # the default search_path is a string, change it to a list
    if not isinstance(args.search_path, list):
        args.search_path = [args.search_path]

    # the debug mode will override the default CSV generation
    if args.debug:
        args.output = None
        print(f"[+] No CSV output file generated in debug mode!")
    else:
        print(f"[+] CSV output file: '{args.output}'")

    # prepare the CSV output file
    csv_file = None
    if args.output:
        csv_file = CSVFile(args.output)

    # look over the different run directories
    for dir_name in args.search_path:
        parse_rundir(dir_name, csv_file)

    # Save the output CSV file
    if args.output:
        csv_file.save()

