#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, re
import numpy as np
from collections import defaultdict

class PathBuilder(object):
    """Create a intermediate object to easily manipulate a path object.

    Args:
        path  (obj): ``Path`` object from the timing report parsing.
        net   (obj): ``VprNetParser`` object to get the block identififer.
        place (obj): ``VprPlaceParser`` object to get the block coordinates.
        blif  (obj): ``BlifParser`` object to map the Verilog netlist.
    """

    def __init__(self, path, net, place, blif=None, precision=3):
        # objects need to build the path class
        self._path          = path
        self._net           = net
        self._place         = place
        self._blif          = blif
        self._precision     = precision
        # inherit from the original Path object
        self.id             = path.id
        self.start_point    = path.startpoint
        self.end_point      = path.endpoint
        self.type           = path.type
        self.slack_time     = f"{path.slack_time:.{precision}f}"
        self.arrival_time   = f"{path.arrival_time:.{precision}f}"
        self.required_time  = f"{path.required_time:.{precision}f}"
        self.slack_time     = f"{path.slack_time:.{precision}f}"
        # path description
        self.start_inst     = None  # blif
        self.end_inst       = None  # blif
        self.start_pb       = None  # blif/net
        self.end_pb         = None  # blif/net
        # path statistics
        self.subckts        = None
        self.nb_points      = None
        self.nb_pbs         = None
        self.path_time      = None
        self.net_time       = None
        self.pb_time        = None
        # path distances
        self.start_coords   = None  # place
        self.end_coords     = None  # place
        self.euclidean_dist = None  # place
        self.manhattan_dist = None  # place
        self.pb2pb_dist     = None  # place
        # extract values
        self.get_block_place()
        self.get_statistics()
        self.get_distances()

    def __len__(self):
        """Return the total number of points."""
        return len(self._path)

    def __getitem__(self, idx):
        """Use this class as a list, in order to iterate each point."""
        return self._path[idx]

    def _get_instance_name(self, point):
        """Return a better instance name related to the RTL file."""
        # if there is no BLIF file used
        if self._blif is None:
            return point['point']
        # .latch, .names, .output
        pb_type = point['node_type']
        if pb_type.startswith('.'):
            if pb_type == ".output":
                pin_name = '.'.join(point['point'].split('.')[:-1])
            elif pb_type == ".input":
                pin_name = "in:"+'.'.join(point['point'].split('.')[:-1])
            else:
                pin_name = self._blif.get_pin(point['point'], pb_type[1:])
            # FIXME: quick for techmap of DSP...
            if "$techmap" in pin_name:
                pin_name = '.'.join(point['point'].split('.')[:-1])
        # subckt: bram, dsp, ...
        else:
            pin_name = self._blif.get_instance(point['point'])
            if pin_name is None:
                pin_name = pb_type
        # clean possible name changes due to ABC, ...
        word_remove = ["$abc", "$auto", "$flatten", "\\"]
        for word in word_remove:
            pin_name = pin_name.replace(word, "")
        word_remove = ["$aiger\d+", "\$\d+"]
        for word in word_remove:
            pin_name = re.sub(word, "", pin_name)
        return pin_name

    def _get_pb_name(self, point):
        """Return a better PB name."""
        # better PB type naming
        types = {
            '.names' : "lut",
            '.latch' : "ff",
            '.input' : "in",
            '.output': "out",
        }
        node_type = point['node_type']
        # subckt
        if not node_type in types:
            return f"{node_type}[{point['pb_id']}]"
        # others
        return f"{types[node_type]}[{point['pb_id']}]"

    def get_block_place(self):
        """Create a table of point with additional information."""
        # for each point in the path
        for point in self._path:
            block  = self._net.get_block(point['point'])
            coords = self._place.get_coordinates(block.get('pb_id'))
            point.update({
                'pb_id'     : block.get('pb_id'),
                'pb_coords' : "({0:2},{1:2})".format(*coords),
                'x'         : coords[0],
                'y'         : coords[1],
            })
        # update object
        self.start_inst = self._get_instance_name(self._path[0])
        self.end_inst   = self._get_instance_name(self._path[-1])
        self.start_pb   = self._get_pb_name(self._path[0])
        self.end_pb     = self._get_pb_name(self._path[-1])

    def get_statistics(self):
        """Evaluate path timings and inter-blocks."""
        nb_pbs, net_time, pb_time = 0, 0, 0
        path_time   = self._path[-1]['t_sum'] - self._path[0]['t_sum']
        prev_pb_id  = self._path[0]['pb_id']
        subckts     = []
        # for each point in the path
        for point in self._path[1:]:
            if point['pb_id'] == prev_pb_id:
                pb_time  += point['t_incr']
            else:
                net_time += point['t_incr']
                nb_pbs   += 1
            prev_pb_id = point['pb_id']
            # check if there is a subckt in the path
            subckts.append(point['node_type'])
        # when there is only one block
        nb_pbs -= 1 if nb_pbs >= 1 else 0
        subckts = set([s for s in subckts[:-1] if not s.startswith('.')])
        # update the object
        self.subckts    = ','.join(list(subckts))
        self.nb_points  = len(self._path[1:-1])
        self.nb_pbs     = nb_pbs
        self.path_time  = f"{path_time:.{self._precision}f}"
        self.net_time   = f"{net_time:.{self._precision}f}"
        self.pb_time    = f"{pb_time:.{self._precision}f}"

    def get_distances(self):
        """Evaluate the Manhattan distance regarding to point placement."""
        # Manhattan distance
        x1, y1 = self._path[0]['x'], self._path[0]['y']
        x2, y2 = self._path[-1]['x'], self._path[-1]['y']
        mw, mh = np.abs(x1 - x2), np.abs(y1 - y2)
        # block-to-block distance
        dw, dh = 0, 0
        for point in self._path[1:]:
            x2, y2 = point['x'], point['y']
            dw    += np.abs(x1 - x2)
            dh    += np.abs(y1 - y2)
            x1, y1 = x2, y2
        # update object
        self.start_coords   = self._path[0]['pb_coords']
        self.end_coords     = self._path[-1]['pb_coords']
        self.euclidean_dist = np.sqrt(mw**2 + mh**2)
        self.manhattan_dist = mw+mh
        self.pb2pb_dist     = dw+dh

