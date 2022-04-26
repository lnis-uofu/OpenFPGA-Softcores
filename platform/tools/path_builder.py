#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np


class PathBuilder(object):
    """
    Create a intermediate object to easily manipulate a path object.
    """

    def __init__(self, path, net, place):
        # objects need to build the path class
        self._path          = path
        self._net           = net
        self._place         = place
        # inherit from the original Path object
        self.id             = path.id
        self.startpoint     = path.startpoint
        self.endpoint       = path.endpoint
        self.type           = path.type
        self.arrival_time   = path.arrival_time
        self.required_time  = path.required_time
        self.slack_time     = path.slack_time
        # path description
        self.start_pb       = None
        self.end_pb         = None
        # path statistics
        self.nb_points      = None
        self.nb_pbs         = None
        self.path_time      = None
        self.net_time       = None
        self.pb_time        = None
        # path distances
        self.euclidean_dist = None
        self.manhattan_dist = None
        self.pb2pb_dist     = None
        self.ratio_dist     = None
        # extract values
        self.get_placements()
        self.get_statistics()
        self.get_distances()

    def __len__(self):
        """Return the total number of points."""
        return len(self._path)

    def __getitem__(self, idx):
        """Use this class as a list, in order to iterate each point."""
        return self._path[idx]

    def get_placements(self):
        """Create a table of point with additional information."""
        # for each point in the path
        for point in self._path:
            block   = self._net.find_block(point['point'])
            x,y,sub = self._place.get_coordinates(block.id)
            point.update({
                'inst'      : block.pin_name,
                'pb_direct' : block.direction[:-3],
                'pb_type'   : block.type,
                'pb_id'     : block.id,
                'coords'    : f"({x:2},{y:2})",
                'x'         : x,
                'y'         : y,
            })
        # update object
        self.start_pb   = "{pb_type}[{pb_id}]".format(**self._path[0])
        self.end_pb     = "{pb_type}[{pb_id}]".format(**self._path[-1])

    def get_statistics(self):
        """Evaluate path timings and inter-blocks."""
        self.nb_points  = len(self._path[1:-1])
        self.nb_pbs     = 0
        self.path_time  = self._path[-1]['t_sum'] - self._path[0]['t_sum']
        self.net_time   = 0
        self.pb_time    = 0
        prev_pb_id      = self._path[0]['pb_id']
        # for each point in the path
        for point in self._path[1:]:
            if point['pb_id'] == prev_pb_id:
                self.pb_time  += point['t_incr']
            else:
                self.net_time += point['t_incr']
                self.nb_pbs   += 1
            prev_pb_id = point['pb_id']
        # when there is only one block
        self.nb_pbs -= 1 if self.nb_pbs >= 1 else 0

    def get_distances(self):
        """Evaluate the Manhattan distance regarding to point placement."""
        # Manhattan distance
        x1, y1 = self._path[0]['x'], self._path[0]['y']
        x2, y2 = self._path[-1]['x'], self._path[-1]['y']
        mw, mh = np.abs(x1 - x2), np.abs(y1 - y2)
        # block-to-block distance
        dw, dh = 0, 0
        for line in self._path[1:]:
            x2, y2 = line['x'], line['y']
            dw    += np.abs(x1 - x2)
            dh    += np.abs(y1 - y2)
            x1, y1 = x2, y2
        # update object
        self.euclidean_dist = np.sqrt(mw**2 + mh**2)
        self.manhattan_dist = mw+mh
        self.pb2pb_dist     = dw+dh
        self.ratio_dist     = (dw+dh)/float(mw+mh) if mw+mh != 0 else 1.0

