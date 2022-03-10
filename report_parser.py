#!/usr/bin/env python3

"""
Just another Python report parser of Yosys and VPR results and reports.
"""

import os
import csv
import argparse
from glob import glob
from softcores.parsers import (YosysReport, VprReport, OpenfpgaShell,
                               TaskLogger, PicosocReport)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description     = __doc__,
        formatter_class = argparse.RawTextHelpFormatter
    )
    # positional arguments
    ap.add_argument('search_path', nargs='*', metavar='<search-path>',
                    help="Specify a base directory to search reports (default: '%(default)s')",
                    default=os.path.join("run_dir", "latest"))
    # optional arguments
    ap.add_argument('-d', '--debug', action='store_true', dest='debug',
                    help="Enable debug mode")
    ap.add_argument('-o', '--output', nargs='?', metavar="<csv-file>", dest="csv",
                    help="Save in CSV format (default: %(default)s)",
                    default="report_parser.csv")
    # parse the user arguments
    args = ap.parse_args()

    # default argument is a string
    if not isinstance(args.search_path, list):
        args.search_path = [args.search_path]

    # for the CSV format
    if args.csv:
        print(f"[+] CSV output file: '{args.csv}'")
        csv_contents = []
        csv_headers  = []
    else:
        print("[-] Warning: no CSV output specified!")

    for rundir in args.search_path:
        # create a line of the csv file
        if args.csv:
            csv_row = {}
        # simulation parameters
        params = OpenfpgaShell(basedir=rundir)
        if args.debug:
            print(params)
        if args.csv:
            csv_headers = list(set([f"params.{h}" for h in params.results.keys()] + csv_headers))
            csv_row.update({f"params.{k}": v for k, v in params.results.items()})
        # OpenFPGA task logger
        task = TaskLogger(basedir=rundir)
        if args.debug:
            print(task)
        if args.csv:
            csv_headers = list(set([f"params.{h}" for h in task.results.keys()] + csv_headers))
            csv_row.update({f"params.{k}": v for k, v in task.results.items()})
        # Softcore top module
        core = PicosocReport(basedir=rundir)
        if args.debug:
            print(core)
        if args.csv:
            csv_headers = list(set([f"params.{h}" for h in core.results.keys()] + csv_headers))
            csv_row.update({f"params.{k}": v for k, v in core.results.items()})
        # Yosys logger
        yosys = YosysReport(basedir=rundir)
        if args.debug:
            print(yosys)
        if args.csv:
            csv_headers = list(set([f"yosys.{h}" for h in yosys.results.keys()] + csv_headers))
            csv_row.update({f"yosys.{k}": v for k, v in yosys.results.items()})
        # VPR logger and results
        vpr = VprReport(basedir=rundir)
        if args.debug:
            print(vpr)
        if args.csv:
            csv_headers = list(set([f"vpr.{h}" for h in vpr._logger.results.keys()] + csv_headers))
            csv_row.update({f"vpr.{k}": v for k, v in vpr._logger.results.items()})
            csv_headers = list(set([f"vpr.{h}" for h in vpr._result.results.keys()] + csv_headers))
            csv_row.update({f"vpr.{k}": v for k, v in vpr._result.results.items()})
        # add a new csv line
        if args.csv:
            csv_contents.append(csv_row)
        print(f"[+] '{rundir}' content parsed!")

    # create the output csv file
    if args.csv:
        with open(args.csv, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(csv_headers))
            writer.writeheader()
            writer.writerows(csv_contents)

