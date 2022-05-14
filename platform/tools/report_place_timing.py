#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Report timing placer: add physical block information (type, ID, positions) of
each point of paths listed in the report timing file genated by VPR.
"""

import os
import sys
import argparse
from glob import glob

# 'tools/' is a sibling folders of 'parsers/', the following command ensures
# the import of libraries from the sibling folder.
sys.path.append(os.path.dirname(os.path.abspath(os.path.join(__file__, ".."))))

from parsers.vpr_report_timing_parser import VprReportTimingParser
from parsers.vpr_net_parser import VprNetParser
from parsers.vpr_place_parser import VprPlaceParser
from tools.path_builder import PathBuilder, PBLocator

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
        metavar = "<rpt-file>",
        help    = "analyze all paths in the report file and save them",
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

## Print data (list of dict) in a table format
def print_table(data, headers, sepwidth=2, precision=3, stream=sys.stdout):
    # measure column widths
    widths = [len(h[1]) for h in headers]
    for row in data:
        for idx, (col, _) in enumerate(headers):
            if isinstance(row[col], float):
                widths[idx] = max(widths[idx], len(f"{row[col]:.{precision}f}"))
            else:
                widths[idx] = max(widths[idx], len(str(row[col])))
    # print headers
    head = (' '*sepwidth).join([f"{h[1]:{w}}" for h, w in zip(headers, widths)])
    print(head, file=stream)
    print("-"*len(head), file=stream)
    # print table
    for idx, row in enumerate(data):
        line = []
        for (col, _), w in zip(headers, widths):
            if isinstance(row[col], float):
                line.append(f"{row[col]:{w}.{precision}f}")
            else:
                line.append(f"{row[col]:{w}}")
        print((' '*sepwidth).join(line), file=stream)
    print("-"*len(head), file=stream)

## Print statistics of the path
def print_statistics(path, stream=sys.stdout):
    data = path.__dict__
    print("Path PB-to-PB : {start_pb} -> {end_pb} (inter-PB: {nb_pbs})".format(**data), file=stream)
    print("Arrival time  : {arrival_time}".format(**data), file=stream)
    print("Path time     : {path_time} (net: {net_time}, pb: {pb_time})".format(**data), file=stream)
    print("Distances     : {manhattan_dist} (Manhattan), {pb2pb_dist} (PB-to-PB)".format(**data), file=stream)

## Print a given path using a table format
def print_path(path, stream=sys.stdout):
    # path description
    print(f"# Path {path.id}", file=stream)
    print(f"Startpoint: {path.start_point}", file=stream)
    print(f"Endpoint  : {path.end_point}", file=stream)
    print(f"Path Type : {path.type}\n", file=stream)
    # create the header structure
    headers = [
        ('point'    , "Point"),     # point name
        ('t_incr'   , "Incr"),      # inter-point path time
        ('t_sum'    , "Path"),      # cumulated path time
        ('node_type', "PB Type"),   # physical block type
        ('pb_id'    , "Block"),     # block identifier
        ('pb_coords', "Coords"),    # block coordinates
    ]
    print_table(path, headers, stream=stream)
    print_statistics(path, stream=stream)
    # separte path in the output file
    if stream is not sys.stdout:
        print(file=stream)

# ============================================================================
#  Main function
# ============================================================================

def main():
    # save user arguments
    args = parse_args()

    # setup/hold report timing file
    setuphold = "hold" if args.hold else "setup"
    prepack   = "pre_pack." if args.pre_pack else ""

    # glob search
    searchdir = os.path.join(args.search_path, "**")
    timing    = find_filename(searchdir, f"{prepack}report_timing.{setuphold}.rpt")
    net       = find_filename(searchdir, "*.net")
    place     = find_filename(searchdir, "*.place")

    # parsers
    if args.output:
        print(f"[+] Parse report files in '{searchdir}'.")
    timing    = VprReportTimingParser(timing)
    net       = VprNetParser(net)
    place     = VprPlaceParser(place)
    pbloc     = PBLocator(net, place)

    # save all paths in a report file
    if args.output:
        # create the output directory if it's not existing
        dirname = os.path.abspath(os.path.dirname(args.output))
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        # create the file
        with open(args.output, 'w') as fp:
            for path in timing:
                percentage = 100 * path.id / float(len(timing))
                print(f"[+] Path analyzed: {path.id}/{len(timing)} ({percentage:.2f}%).", end='\r', flush=True)
                path_ext = PathBuilder(path, None, pbloc)
                print_path(path_ext, stream=fp)
            print()
        print(f"[+] Output report generated: '{args.output}'")
    # single path printing (stdout)
    else:
        path = timing[args.path_id-1 if args.path_id > 1 else 0]
        path = PathBuilder(path, None, pbloc)
        print_path(path)


if __name__ == "__main__":
    main()

