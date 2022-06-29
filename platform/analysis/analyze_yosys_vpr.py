#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quick result analysis of Yosys and VPR generated files.

>>> ./analyze_yosys_vpr.py <yosys-vpr-result-file> \\
        --param-file <test-params> \\
        --labels device_layout \\
        --annotate \\
        --legend \\
        --fig-size 8x5
"""

import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================================
#  Command-line arguments
# ============================================================================

ap = argparse.ArgumentParser(
    description     = __doc__,
    formatter_class = argparse.RawTextHelpFormatter
)
# Positional arguments
ap.add_argument(
    'yosys_vpr_result_file',
    metavar = "<yosys-vpr-result-file>",
    help    = "Name of the Yosys and VPR report (CSV) file to analyze")
# Optional arguments
ap.add_argument(
    '--param-file',
    metavar = "<file>",
    help    = "Name of the parameter file to label the data")
ap.add_argument(
    '-x', '--x-axis',
    metavar = "<column>",
    default = "vpr.critical_path",
    help    = "Column name to be printed on the X-axis (default: %(default)s)")
ap.add_argument(
    '-y', '--y-axis',
    metavar = "<column>",
    default = "vpr.channel_width",
    help    = "Column name to be printed on the Y-axis (default: %(default)s)")
ap.add_argument(
    '-l', '--labels',
    metavar = "<column>",
    default = "params.memory_size",
    help    = "Column name to be printed with labels (default: %(default)s)")
ap.add_argument(
    '--annotate',
    action  = 'store_true',
    default = False,
    help    = "Annotate with point with labels (default: %(default)s)")
ap.add_argument(
    '--legend',
    action  = 'store_true',
    default = False,
    help    = "Add the legend on the figure (default: %(default)s)")
ap.add_argument(
    '--fig-size',
    metavar = "<width>x<height>",
    default = "5x5",
    help    = "Figure dimensions (default: %(default)s)")
ap.add_argument(
    '-o', '--output',
    metavar = "<file>",
    default = os.path.join("outputs", "figures", "yosys_vpr.pdf"),
    help    = "Directory to save the generated figure (default: %(default)s)")
# Parse the user arguments
args = ap.parse_args()

# ============================================================================
#  Main program
# ============================================================================

# Create ouput dir
if not os.path.isdir(os.path.dirname(args.output)):
    os.makedirs(os.path.dirname(args.output))

# Figure properties
fig_width, fig_height = args.fig_size.split('x')
fig, ax = plt.subplots(figsize=(int(fig_width), int(fig_height)))
ax.set_title("Yosys-VPR result analysis")
ax.set_xlabel(f"{args.x_axis}")
ax.tick_params(axis="x", rotation=-45)
ax.set_ylabel(f"{args.y_axis}")
ax.set_axisbelow(True)
ax.grid(linestyle='--', linewidth=0.5, zorder=3)

# Read the csv data
df = pd.read_csv(args.yosys_vpr_result_file)
# add the parameters as the end of the DataFrame
if args.param_file:
    param = pd.read_csv(args.param_file)
    df = pd.concat([df, param], axis=1)
# patch the object-type issue with vpr.channel_width
if args.x_axis == 'vpr.channel_width' or args.y_axis == 'vpr.channel_width':
    df['vpr.channel_width'].replace('unroutable', np.nan, inplace=True)
    df = df.dropna(subset=['vpr.channel_width'])
    df['vpr.channel_width'] = df['vpr.channel_width'].astype(int)

# Plot the data
X = df[args.x_axis]
Y = df[args.y_axis]
L = df[args.labels]
# for each unique label values
for label in L.unique():
    x = df[df[args.labels] == label][args.x_axis]
    y = df[df[args.labels] == label][args.y_axis]
    ax.scatter(x, y, label=label)

# Annotate points with the labels
if args.annotate:
    for x, y, l in zip(X, Y, L):
        plt.annotate("{}".format(l),            # text to display
                     (x,y),                     # label coordinates
                     textcoords="offset points",# how to position the text
                     xytext=(0,10),             # distance from text to position
                     fontsize='small',          # label fontsize
                     ha='center')               # label alignment
# Print the legend on the figure
if args.legend:
    ax.legend(framealpha=.5, fontsize='small')

# Save the figure in a PDF format
plt.tight_layout()
plt.savefig(f"{args.output}")
