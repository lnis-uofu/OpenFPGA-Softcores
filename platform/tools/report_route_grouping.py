#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Report route and groups: extends the description of each point composing the
path (PB type, block ID, coordinates, ...) using VPR *.net and *.place reports
and add metrics to provide a more complete routing analysis.
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

## Create group of path according to the startpoint
def create_groups(timing, net, place, precision=3):
    headers = ['id','start','end','start_pb','end_pb','nb_points','nb_pbs',
               'arrival_time','path_time','net_time','pb_time','start_coords',
               'end_coords','manhattan_dist','pb2pb_dist','ratio_dist']
    groups  = OrderedDict()
    total   = len(timing)
    for idx, path in enumerate(timing):
        perc = 100 * idx / float(total)
        print(f"[+] Path analyzed: {idx}/{total} ({perc:.2f}%)   ", end='\r', flush=True)
        path = PathBuilder(path, net, place)
        row  = {
            'id'            : path.id,
            'start'         : path[0]['inst'],
            'end'           : path[-1]['inst'],
            'start_pb'      : path.start_pb,
            'end_pb'        : path.end_pb,
            'nb_points'     : path.nb_points,
            'nb_pbs'        : path.nb_pbs,
            'arrival_time'  : f"{path.arrival_time:.{precision}f}",
            'path_time'     : f"{path.path_time:.{precision}f}",
            'net_time'      : f"{path.net_time:.{precision}f}",
            'pb_time'       : f"{path.pb_time:.{precision}f}",
            'start_coords'  : path[0]['coords'],
            'end_coords'    : path[-1]['coords'],
            'manhattan_dist': path.manhattan_dist,
            'pb2pb_dist'    : path.pb2pb_dist,
            'ratio_dist'    : f"{path.ratio_dist:.{precision}f}",
        }
        # group by startpoint
        if row['start'] in groups:
            groups[row['start']].append(row)
        else:
            groups[row['start']] = [row]
    print()
    return headers, groups

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
    net       = find_filename(searchdir, "*.net")
    place     = find_filename(searchdir, "*.place")

    # parsers
    print(f"[+] Parse report files.")
    timing    = VprReportTimingParser(timing)
    net       = VprNetParser(net)
    place     = VprPlaceParser(place)

    # save all paths in a report file
    if args.output:
        # create group of paths
        print(f"[+] Create group of paths.")
        t_start = time()
        headers, groups = create_groups(timing, net, place)
        print(f"[+] Total elapsed time: {time()-t_start:.2f} s")
        # create the output directory if it's not existing
        dirname = os.path.abspath(os.path.dirname(args.output))
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        # create the file
        with open(args.output, 'w') as fp:
            wr = csv.DictWriter(fp, fieldnames=headers)
            wr.writeheader()
            for start, paths in groups.items():
                for path in paths:
                    wr.writerow(path)
        print(f"[+] Output report generated: '{args.output}'")
    else:
        path = timing[args.path_id-1 if args.path_id > 1 else 0]
        headers, groups = create_groups([path], net, place)
        print_path(headers, list(groups.items())[0][1][0])


if __name__ == "__main__":
    main()

