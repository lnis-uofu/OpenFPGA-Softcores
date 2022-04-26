#!/usr/bin/env python3

import os, re, time
import numpy as np
from collections import OrderedDict

class Path(list):
    """
    Define the path object to store path properties and manipulate each point
    composing the path like a Python list object.
    """
    def __init__(self, *args, **kwargs):
        # inherit from a list type
        list.__init__(self, *args)
        # path properties
        self.id             = kwargs.get('id', None)
        self.startpoint     = kwargs.get('startpoint', None)
        self.endpoint       = kwargs.get('endpoint', None)
        self.type           = kwargs.get('type', None)
        self.arrival_time   = kwargs.get('arrival_time', None)
        self.required_time  = kwargs.get('required_time', None)
        self.slack_time     = kwargs.get('slack_time', None)


class VprReportTimingParser(object):
    """
    Parse a report timing file (generated by VPR) to analyze paths and theirs
    point through which they pass. This object store each Path object like a
    list item that could be accessed by iteration.
    When the paths are grouped, this enables to reconstruct the connection
    tree of each signal in order to perform the routing congestion of the
    design.

    Note: all paths composing the design is printed thanks to the following
    VPR option: `--timing_report_npaths -1`.
    """

    # Regex to extract file information
    _rScale         = r'# Unit scale: (?P<unit_scale>[^\s]+) seconds'
    _rPrecision     = r'# Output precision: (?P<unit_precision>\d+)'

    # Regex to extract path description
    _rPathId        = r'#Path (?P<id>\d+)'
    _rStartpoint    = r'Startpoint:\s+(?P<startpoint>[^\s]+)'
    _rEndpoint      = r'Endpoint\s*:\s+(?P<endpoint>[^\s]+)'
    _rPathType      = r'Path Type\s*:\s+(?P<type>[^\s]+)'

    # Regex to extract point structures
    _rPoint         = r'(?P<point>[^\s]+)'
    _rNodeType      = r'\((?P<node_type>[\w\.]+)\s*(at \((?P<x>\d+),(?P<y>\d+)\))?\)'
    _rEdgeClock     = r'(\[(?P<edge_clock>[\w\-]+)\])?'
    _rIncr          = r'(?P<t_incr>[\d\.\-]+)'
    _rSum           = r'(?P<t_sum>[\d\.\-]+)'
    _rNet           = r'\|\s+\((?P<net>.+)\)'
    _rArrivalTime   = r'data arrival time\s+(?P<arrival_time>[\d\.]+)'
    _rRequiredTime  = r'data required time\s+(?P<required_time>[\d\.\-]+)'
    _rSlackTime     = r'slack\s+\((?P<constraint>\w+)\)\s+(?P<slack_time>[\d\.\-]+)'

    # Regex to start/end the parsing
    _rPathPoint     = _rPoint+r'\s+'+_rNodeType+'\s+'+_rEdgeClock+r'\s+'+_rIncr+r'\s+'+_rSum
    _rPathNet       = _rNet+r'\s+'+_rIncr+r'\s+'+_rSum
    _rStartToken    = r'{}\s+'+_rNodeType+'\s+'+_rEdgeClock+r'\s+'+_rIncr+r'\s+'+_rSum
    _rEndToken      = r'{}\s+'+_rNodeType+r'\s+'+_rIncr+r'\s+'+_rSum

    # Compiled regexes (for faster parsing)
    _rcScale        = re.compile(_rScale)
    _rcPrecision    = re.compile(_rPrecision)
    _rcPathId       = re.compile(_rPathId)
    _rcStartpoint   = re.compile(_rStartpoint)
    _rcEndpoint     = re.compile(_rEndpoint)
    _rcPathType     = re.compile(_rPathType)
    _rcPathPoint    = re.compile(_rPathPoint)
    _rcPathNet      = re.compile(_rPathNet)
    _rcArrivalTime  = re.compile(_rArrivalTime)
    _rcRequiredTime = re.compile(_rRequiredTime)
    _rcSlackTime    = re.compile(_rSlackTime)

    # Post-formatting of the file header information
    _file_info = [
        (_rcScale,          'unit_scale',       float),
        (_rcPrecision,      'unit_precision',   int),
    ]

    # Post-formatting of the path description
    _path_desc = [
        (_rcPathId,         'id',               int),
        (_rcStartpoint,     'startpoint',       str),
        (_rcEndpoint,       'endpoint',         str),
        (_rcPathType,       'type',             str),
        (_rcArrivalTime,    'arrival_time',     float),
        (_rcRequiredTime,   'required_time',    float),
        (_rcSlackTime,      'slack_time',       float),
    ]

    # Post-formatting of a point in the path
    _path_point_fmt = {
        'point'         : str,
        'node_type'     : str,
        'x'             : str,
        'y'             : str,
        'edge_clock'    : str,
        't_incr'        : float,
        't_sum'         : float,
    }

    # Post-formatting of a net in the path
    _path_net_fmt = {
        'net'           : str,
        't_incr'        : float,
        't_sum'         : float,
    }

    def __init__(self, filename, nb_paths=None):
        self.filename   = filename
        self.nb_paths   = nb_paths      # save time by reading the first paths
        self.fileinfo   = dict()        # store all file information
        self.paths      = list()        # list all paths of the files
        self.groups     = OrderedDict() # list all group of paths
        self.stats      = OrderedDict() # store statistics of paths
        self.parse()
        self.get_groups()
        self.get_stats()

    def __str__(self):
        """For debbuging purpose: print(object)."""
        tim = []
        for p in self.paths:
            tim.append(f"{p.id:3}| slack: {p.slack_time:.3f}, start: {p.startpoint}, end: {p.endpoint}, points: {len(p)}")
        return '\n'.join(tim)

    def __len__(self):
        """Return the total number of paths."""
        return self.nb_paths

    def __getitem__(self, idx):
        """Use this class as a list, in order to iterate each path."""
        return self.paths[idx]

    def parse(self, precision=3):
        """Parse the report file using the class regex."""
        # Get file updated date and time
        self.fileinfo['modified_datetime'] = time.ctime(os.path.getmtime(self.filename))
        # Parse the report timing file
        with open(self.filename, 'r') as fp:
            path   = Path()
            t_incr = 0
            token  = False
            for line in fp.readlines():
                line = line.rstrip()
                # file information
                for regex, attrib, fmt in self._file_info:
                    m = regex.match(line)
                    if m:
                        self.fileinfo[attrib] = fmt(m.groupdict()[attrib])
                if "unit_precision" in self.fileinfo:
                    precision = self.fileinfo['unit_precision']
                # path description
                for regex, attrib, fmt in self._path_desc:
                    m = regex.match(line)
                    if m and getattr(path, attrib) is None:
                        setattr(path, attrib, fmt(m.groupdict()[attrib]))
                # end of path / loop breaker
                if self._rcSlackTime.match(line):
                    # append the current path
                    self.paths.append(path)
                    # save processing time by reading a given number of paths
                    if self.nb_paths is not None:
                        if path.id >= self.nb_paths:
                            break
                    # reset the new pathh
                    path = Path()
                # list of points (and nets) in the path
                if path.startpoint is None or path.endpoint is None:
                    continue
                # from the startpoint...
                regex = self._rStartToken.format(re.escape(path.startpoint))
                if re.match(regex, line) and not token:
                    token = True
                # ...for each point...
                m = self._rcPathPoint.match(line)
                if m and token:
                    # add a new point in the path list
                    point = {}
                    for key, val in m.groupdict().items():
                        if val is None:
                            continue
                        if not key in self._path_point_fmt:
                            continue
                        fmt = self._path_point_fmt[key]
                        point[key] = fmt(val)
                    if point['t_incr'] < t_incr:
                        fmt = self._path_point_fmt['t_incr']
                        val = "{:.{p}f}".format(t_incr, p=precision)
                        point['t_incr'] = fmt(val)
                    path.append(point)
                if m:
                    t_incr = 0
                # ...for each net...
                m = self._rcPathNet.match(line)
                if m:
                    net = {}
                    for key, val in m.groupdict().items():
                        if val is None:
                            continue
                        if key in self._path_net_fmt:
                            fmt = self._path_net_fmt[key]
                            net[key] = fmt(val)
                    # keep incrementing the time to prevent missing net delays
                    t_incr += net['t_incr']
                # ...to the endpoint
                regex = self._rEndToken.format(re.escape(path.endpoint))
                if re.match(regex, line) and token:
                    token = False
            # update the total number of paths
            self.nb_paths = len(self.paths)

    def get_groups(self):
        """Create groups of signal (bus) for high-level routing analysis."""
        for p in self.paths:
            if p.startpoint in self.groups:
                self.groups[p.startpoint]['end_list'].append(p.endpoint)
                self.groups[p.startpoint]['total'] += 1
                continue
            self.groups[p.startpoint] = {
                'end'       : p.endpoint,
                'end_list'  : [p.endpoint],
                'total'     : 1,
            }

    def get_stats(self):
        # Calculate statistics
        if not self.paths:
            return
        high = self.paths[0].arrival_time
        low  = self.paths[-1].arrival_time
        self.stats.update({
            'highest_arrival_time'  : high,
            'lowest_arrival_time'   : low,
            'arrival_time_deviation': np.abs(high) - np.abs(low),
        })

    def print_groups(self, debug=False):
        for start, count in self.groups.items():
            print(f"{count['total']:3} paths, {start} -> {count['end']}")
            if debug:
                for p in count['end_list'][1:]:
                    print(f"{' '*(12+len(start))}-> {p}")

    def print_stats(self):
        width = 25
        if "modified_datetime" in self.fileinfo:
            print(f"modified_datetime{' '*(width-17)}: {self.fileinfo['modified_datetime']}")
        if "unit_scale" in self.fileinfo:
            print(f"unit_scale{' '*(width-10)}: {self.fileinfo['unit_scale']} seconds")
        for stat, values in self.stats.items():
            print(f"{stat}{' '*(width-len(stat))}: {values:8.4f}")


## Quick and dirty unit test
if __name__ == "__main__":
    import argparse
    from pprint import pprint

    # Parse all arguments
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('report_filename', type=str,
                    help="VPR timing report file to parse")
    ap.add_argument('-d', '--debug', action='store_true',
                    help="print the full content of the path list")
    ap.add_argument('-n', '--nb-paths', metavar='<#-of-paths>', type=int,
                    help="number of paths to display (default: %(default)s)",
                    default=100)
    ap.add_argument('-s', '--stats', action='store_true',
                    help="print only statistics")
    args = ap.parse_args()

    rpt = VprReportTimingParser(args.report_filename, args.nb_paths)
    if args.debug and not args.stats:
        for path in rpt.paths:
            print(f"Path {path.id}")
            for point in path:
                print(f"    ", end="")
                print(point)
    # print all paths
    if not args.stats:
        print(f"**********  LIST OF PATHS (TOP: {args.nb_paths})  **********")
        print(rpt)
    print(f"**********  GROUP OF PATHS (TOP: {args.nb_paths})  **********")
    rpt.print_groups(debug=args.debug)
    print("**********  STATISTICS  **********")
    rpt.print_stats()
