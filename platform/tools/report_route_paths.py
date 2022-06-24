#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Report path after route step: extends the description of each point composing
the path (PB type, block ID, coordinates, ...) using Yosys *.eblif file, and
VPR *.net and *.place reports and add metrics to provide a more complete
routing analysis.
"""

import os
import sys
import csv
import argparse
from time import time
from glob import glob
from collections import OrderedDict

# 'tools/' is a sibling folders of 'parsers/', the following command ensures
# the import of libraries from the sibling folder.
sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, ".."))))

from parsers.vpr_report_timing_parser import VprReportTimingParser
from parsers.vpr_net_parser import VprNetParser
from parsers.vpr_place_parser import VprPlaceParser
from parsers.blif_parser import BlifParser
from tools.path_builder import PathBuilder

# ============================================================================
#  Command-line arguments
# ============================================================================

def parse_args():
    ap = argparse.ArgumentParser(
        description     = __doc__,
        formatter_class = argparse.RawTextHelpFormatter,
    )
    # positional arguments
    ap.add_argument(
        'search_path',
        metavar = '<search-path>',
        default = os.path.join("run_dir", "latest"),
        help    = "root path to recursively search report files (default: '%(default)s')",
    )
    # optional arguments
    ap.add_argument(
        '-d', '--debug',
        action  = 'store_true',
        help    = "enable debug mode",
    )
    ap.add_argument(
        '-p', '--path-id',
        type    = int,
        metavar = "<path-id>",
        default = 0,
        help    = "define the path number to print (default: %(default)s)",
    )
    ap.add_argument(
        '--hold',
        action  = 'store_true',
        help    = "parse the hold report timing file",
    )
    ap.add_argument(
        '--pre-pack',
        action  = 'store_true',
        help    = "parse the pre-pack report timing file",
    )
    ap.add_argument(
        '-o', '--output',
        metavar = "<csv-file>",
        help    = "save all paths in a given CSV file (default: %(default)s)",
    )
    # return the user arguments
    return ap.parse_args()

# ============================================================================
#  Functions
# ============================================================================

## Find a filename in a root path, using a recursive approach
def find_filename(path, filename):
    file = glob(os.path.join(path, filename), recursive=True)
    if not file:
        print(f"[-] File '{filename}' not found in '{path}'.")
        sys.exit(1)
    return file[0]

## Create a list of paths with extended information
def create_paths(timing, net, place, blif, precision=3):
    headers = [
        # report_timing
        'id','start_point','end_point',
        # Yosys (*.eblif)
        'start_inst','end_inst',
        # Packer (*.net)
        'start_pb','end_pb', 'subckts',
        # Placer (*.place)
        'start_coords','end_coords','nb_points','nb_pbs',
        'manhattan_dist','pb2pb_dist',
        # Router (report_timing)
        'slack_time','arrival_time','path_time','net_time','pb_time',
    ]
    table = []
    total = len(timing)
    # for each path in the timing report
    for idx, path in enumerate(timing):
        perc = 100 * (idx+1) / float(total)
        print(f"[+] Path analyzed: {idx+1}/{total} ({perc:.2f}%)   ", end='\r', flush=True)
        path = PathBuilder(path, net, place, blif, precision)
        table.append({h:path.__dict__[h] for h in headers})
    print()
    return headers, table

## Print a given path
def print_path(headers, path):
    width = max([len(h) for h in headers])
    for header in headers:
        print(f"{header:{width}} : {path[header]}")

# ============================================================================
#  Main function
# ============================================================================

def main():
    # user arguments
    args      = parse_args()

    # setup/hold report timing file
    setuphold = "hold" if args.hold else "setup"
    prepack   = "pre_pack." if args.pre_pack else ""

    # glob search
    searchdir = os.path.join(args.search_path, "**")
    timing    = find_filename(searchdir, f"{prepack}report_timing.{setuphold}.rpt")
    eblif     = find_filename(searchdir, "*.eblif")
    blif      = find_filename(searchdir, "*.blif")
    net       = find_filename(searchdir, "*.net")
    place     = find_filename(searchdir, "*.place")

    # parsers
    print(f"[+] Parse report files in '{searchdir}'.")
    t_start = time()
    timing    = VprReportTimingParser(timing)
    blif      = BlifParser(eblif if eblif else blif)
    net       = VprNetParser(net)
    place     = VprPlaceParser(place)
    print(f"[+] Total parsing time: {time()-t_start:.2f} s")

    # save all paths in a report file
    if args.output:
        # extend the description for all paths of the timing report
        t_start = time()
        headers, table = create_paths(timing, net, place, blif)
        print(f"[+] Total analysis time: {time()-t_start:.2f} s")
        # create the output directory if it's not existing
        dirname = os.path.abspath(os.path.dirname(args.output))
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        # create the file
        with open(args.output, 'w') as fp:
            wr = csv.DictWriter(fp, fieldnames=headers)
            wr.writeheader()
            wr.writerows(table)
        print(f"[+] Output CSV generated: '{args.output}'")
    # print a single path
    else:
        path = timing[args.path_id-1 if args.path_id > 1 else 0]
        headers, table = create_paths([path], net, place, blif)
        print_path(headers, table[0])


if __name__ == "__main__":
    main()

