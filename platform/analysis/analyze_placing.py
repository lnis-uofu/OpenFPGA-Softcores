#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This tool provides a post-route path analysis by grouping every paths by
*Physiscal Block* (PB) types (*ff*, *bram*, *io*) or by bus names related to
the RTL description of the soft-core.
"""

import os, csv, argparse
import matplotlib.pyplot as plt
from glob import glob
from path_formatter import PathFormatter

# ============================================================================
#  Command-line arguments
# ============================================================================

ap = argparse.ArgumentParser(
    description     = __doc__,
    formatter_class = argparse.RawTextHelpFormatter
)
# Positional arguments
ap.add_argument(
    'search_path',
    metavar = "<search-path>",
    help    = "Base directory of the report route paths (CSV) files to analyze")
ap.add_argument(
    'param_file',
    metavar = "<param-file>",
    help    = "Name of the parameter file to label the data")
# Optional arguments
ap.add_argument(
    '-s', '--softcore',
    metavar = "<name>",
    default = "PicoRV32",
    help    = "Name of the soft-core design to evaluate (only used for printing) (default: %(default)s)")
ap.add_argument(
    '--fig-size',
    metavar = "<width>x<height>",
    default = "8x5",
    help    = "Figure dimensions (default: %(default)s)")
ap.add_argument(
    '--fig-format',
    default = "pdf",
    choices = ['pdf', 'png', 'svg'],
    help    = "Figure file format (default: %(default)s)")
ap.add_argument(
    '-o', '--output-dir',
    metavar = "<path>",
    default = os.path.join("outputs", "figures"),
    help    = "Directory to save the generated figures (default: %(default)s)")
# Analysis parameters
ap.add_argument(
    '--nb-bus',
    metavar = "<int>",
    type    = int,
    default = 10,
    help    = "Number of group of path (buses) to display (default: %(default)s)")
ap.add_argument(
    '--nb-worst',
    metavar = "<int>",
    type    = int,
    default = 10,
    help    = "Number of critical path to display (default: %(default)s)")
ap.add_argument(
    '--bus-type',
    action  = 'store_true',
    default = False,
    help    = "Print by bus types rather than PB types (default: %(default)s)")
ap.add_argument(
    '--hide-ff2ff',
    action  = 'store_true',
    default = True,
    help    = "Hide FF to FF paths (default: %(default)s)")
# Parse the user arguments
args = ap.parse_args()

# ============================================================================
#  Functions
# ============================================================================

# Generate a plot to evaluate PB types
def plot_pb_types(**kwargs):
    fig, ax = plt.subplots(figsize=fig_size)
    # colors (T10)
    colors = {
        'ff,ff'     : 'tab:gray',
        'ff,bram'   : 'tab:blue',
        'bram,ff'   : 'tab:orange',
        'bram,bram' : 'tab:green',
        'dsp'       : 'black',
        'critical'  : 'red'}
    # vertical bar (critical path)
    plt.axvline(max(df.slack_time), color='red', ls='--')
    # star point (optimal point)
    ax.scatter(0.2, 1, s=320, marker='*', color='green', zorder=3)
    # plot all data
    for start_pb_type in ['ff', 'bram']:
        for end_pb_type in ['ff','bram']:
            if args.hide_ff2ff and start_pb_type == "ff" and end_pb_type == "ff":
                continue
            group = df[(df.start_pb_type == start_pb_type) &
                       (df.end_pb_type == end_pb_type)]
            ax.scatter(group.slack_time, group.ratio_dist,
                       label=f"{start_pb_type} -> {end_pb_type} ({len(group)})",
                       color=colors[f"{start_pb_type},{end_pb_type}"],
                       alpha=.8, marker='.', s=100)
    # DSP points
    group = df[df.subckts.isnull() == False]
    ax.scatter(group.slack_time, group.ratio_dist,
               label=f"dsp instances ({len(group)})",
               marker='+', color=colors['dsp'], s=30)
    # critical path
    ax.scatter(df.slack_time.head(args.nb_worst), df.ratio_dist.head(args.nb_worst),
               label=f"critical path ({args.nb_worst})",
               marker='x', color=colors['critical'], s=30)
    # legend
    ax.legend(loc='lower left', fontsize=9,
              labelspacing=0.05, borderaxespad=0.2, handlelength=1.0)
    return fig, ax

# Generate a plot to evaluate signal bus bottlenecks
def plot_bus_types(**kwargs):
    """Generate a plot """
    fig, ax = plt.subplots(figsize=fig_size)
    # vertical bar (critical path)
    plt.axvline(max(df.slack_time), color='red', ls='--')
    # star point (optimal point)
    ax.scatter(0.2, 1, s=320, marker='*', color='green')
    # DSP points
    group = df[df.subckts.isnull() == False]
    ax.scatter(group.slack_time, group.ratio_dist,
               label=f"dsp instances ({len(group)})",
               marker='+', color='black', s=40, lw=1, zorder=3)
    # critical path
    ax.scatter(df.slack_time.head(args.nb_worst), df.ratio_dist.head(args.nb_worst),
               label=f"critical path ({args.nb_worst})",
               marker='x', color='red', s=25, lw=1, zorder=3)
    # plot all data
    for bus_id in range(args.nb_bus):
        group = df[df.bus_id == bus_id]
        # display shorter names in the legend
        if kwargs.get('short_bus_names', False):
            start_bus = group.start_bus.iloc[0].split('.')[-1]
            end_bus   = group.end_bus.iloc[0].split('.')[-1]
        else:
            start_bus = group.start_bus.iloc[0]
            end_bus   = group.end_bus.iloc[0]
        # display PB types in the legend
        if kwargs.get('show_pb_types', False):
            label = f"{start_bus} [{group.start_pb_type.iloc[0]}] "\
                    f"-> {end_bus} [{group.end_pb_type.iloc[0]}] "\
                    f"({len(group)})"
        else:
            label = f"{start_bus} -> {end_bus} ({len(group)})"
        # plot bus points
        ax.scatter(group.slack_time, group.ratio_dist,
                   label=label,
                   alpha=.8, marker='.', s=100)
    # legend
    ax.legend(loc='lower left', fontsize=7,
              labelspacing=0.05, borderaxespad=0.2, handlelength=1.0)
    return fig, ax

# ============================================================================
#  Main program
# ============================================================================

# Create ouput dir
if not os.path.isdir(args.output_dir):
    os.makedirs(args.output_dir)

# Figure size setup
fig_width, fig_height = args.fig_size.split('x')
fig_size              = (int(fig_width), int(fig_height))

# files to parse
files  = sorted(glob(f"{args.search_path}/report_route_paths*.csv"))
params = csv.DictReader(open(args.param_file, 'r'))
phead  = params.fieldnames

# loop to print all plot for a different design parameters
for fname, pval in zip(files, params.reader):
    # look over various files
    data  = PathFormatter(fname)
    df    = data.df
    param = [f"{h}={v}" for h, v in zip(phead, pval)]
    # plot bus
    if args.bus_type:
        fig, ax = plot_bus_types(
            short_bus_names=False,
            show_pb_types=True)
    else:
        fig, ax = plot_pb_types()
    # figure properties
    ax.set_title(f"Placer analysis of the {args.softcore} with {', '.join(param)}")
    ax.set_xlabel("Arrival Time (ns) (lower is better)")
    ax.set_ylabel("Ratio distance (closer to 1 is better)")
    # save the figure
    plt.tight_layout()
    path_type = "bus_type" if args.bus_type else "pb_type"
    plt.savefig(f"{args.output_dir}/placer_analysis.{path_type}.{'.'.join(param)}.{args.fig_format}")
