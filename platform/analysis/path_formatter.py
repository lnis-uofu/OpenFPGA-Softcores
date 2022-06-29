#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object create a ``DataFrame`` object to pre-process report route paths 
CSV formatted results to manipulate group of buses, to locate bottleneck in 
the RTL design.
"""

import os
import pandas as pd
import numpy as np


class PathFormatter(object):
    """Format for ease data handling for plotting.
    
    Args:
        filename (str): File name of the CSV-format path report, containing 
            every paths in the design and their timings.
    
    Attributes:
        df (DataFrame): result of the formatted data.
    """

    _rename_bram = [r'.*dpram.*', r'.*sram.*', r'.*spram.*']

    def __init__(self, filename, **kwargs):
        self.filename       = filename
        # class attributes
        self.df             = None
        # format data
        self.format_data()
        self.extract_statistics()

    def format_data(self, **kwargs):
        """Format the data with the corresponding filters."""
        # check the file
        if not os.path.isfile(self.filename):
            RuntimeError(f"File not found '{self.filename}'")
        _, ext = os.path.splitext(self.filename)
        if not ext.lower() == "csv" :
            RuntimeError("Wrong file format, must be CSV formatted")
        # read the csv data
        self.df = pd.read_csv(self.filename)
        # change slack time to positive values
        self.df['slack_time']   = np.abs(self.df.slack_time)
        # FIXME: change the number of points and PBS to the full path
        self.df['nb_points']    = self.df.nb_points + 2
        self.df['nb_pbs']       = self.df.nb_pbs + 1
        # extract only PB type, removing the PB ID
        self.df['start_pb_type']= self.df.start_pb.str.extract('([^\[]+)\[\d+\]', expand=True)
        self.df['end_pb_type']  = self.df.end_pb.str.extract('([^\[]+)\[\d+\]', expand=True)
        # rename subckt as a generic BRAM tag
        self.df.start_pb_type.replace(self._rename_bram, "bram", regex=True, inplace=True)
        self.df.end_pb_type.replace(self._rename_bram, "bram", regex=True, inplace=True)
        # rename point instance (memory)
        self.df.start_inst.replace(r"^(.+)\.\d+\.\d+\.\d+$", value=r"\1", regex=True, inplace=True)
        self.df.end_inst.replace(r"^(.+)\.\d+\.\d+\.\d+$", value=r"\1", regex=True, inplace=True)
        # remove Verilog generator artefacts
        self.df.start_inst.replace("\.genblk\d+", "", regex=True, inplace=True)
        self.df.end_inst.replace("\.genblk\d+", "", regex=True, inplace=True)
        # group paths by bus
        self.df['start_bus']    = self.df.start_inst.str.extract('^([^\[]+)\[?', expand=True)
        self.df['end_bus']      = self.df.end_inst.str.extract('^([^\[]+)\[?', expand=True)
        # create unique buses (couple of start and end points)
        self.df['bus_name']     = self.df.start_bus + " -> " + self.df.end_bus
        # create unique bus ID
        uniq_bus                = pd.unique(self.df.bus_name.values.ravel())
        uniq_bus                = pd.Series(np.arange(len(uniq_bus)), uniq_bus)
        self.df['bus_id']       = self.df[['bus_name']].applymap(uniq_bus.get)


    def extract_statistics(self, **kwargs):
        """Generate metrics and statistics to better analyze data."""
        self.df['ratio_pb_point']   = self.df.nb_pbs / self.df.nb_points          # packer (lower is better)
        self.df['ratio_point_pb']   = self.df.nb_points / self.df.nb_pbs          # packer (higher is better)
        self.df['ratio_dist']       = self.df.manhattan_dist / self.df.pb2pb_dist # placer/router (closer to 1 is better)
        self.df['arrival_time_r']   = 1 / self.df.arrival_time
