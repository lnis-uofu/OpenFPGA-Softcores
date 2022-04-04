#!/usr/bin/env python3

import os, re

class Net(list):
    """
    Define the net object to store net properties and manipulate each node
    composing the net like a Python list object.
    """
    def __init__(self, *args, **kwargs):
        # inherit from a list type
        list.__init__(self, *args)
        # net properties
        self.id         = kwargs.get('id', None)
        self.endpoint   = kwargs.get('endpoint', None)
        # alternate arguments
        if self.id is None:
            self.id = kwargs.get('net_id', None)
        if self.endpoint is None:
            self.endpoint = kwargs.get('name', None)


class VprRouteParser(object):
    """
    Parse a route file (generated by VPR) to obtain all nets and their node
    coordinates on the FPGA grid.

    Routing segment keywords:
    - CHANX: horizontal channel
    - CHANY: vertical channel
    - IPIN: input pin
    - OPIN: output pin
    - SINK: sink of a certain input class
    - SOURCE: source of a certain output pin class
    """

    # Define regex to parse file information
    _rcPlaceFile= re.compile(r'Placement_File:\s+([^\s]+)')
    _rcPlaceId  = re.compile(r'Placement_ID:\s+([^\s]+)')
    _rcArraySize= re.compile(r'Array size: (\d+) x (\d+) logic blocks')

    # Define regex for Net, Node and Block parsing
    _rNetId     = '(?P<net_id>\d+)'
    _rEndpoint  = r'\((?P<endpoint>[^\)]+)\)'
    _rNodeId    = r'(?P<node_id>\d+)'
    _rCoords    = r'\((?P<x>\d+),(?P<y>\d+)\)'
    _rCoordsTo  = r'to\s+\((?P<to_x>\d+),(?P<to_y>\d+)\)'
    _rTrack     = r'Track:\s+(?P<track>\d+)'
    _rTracks    = r'Track:\s+\((?P<tracks>(\d+,?\s*)+)\)' # will be: '1, 2, 3, 4'
    _rSwitchId  = r'Switch:\s+(?P<switch_id>[\-\d]+)'
    _rPinId     = r'Pin:\s+(?P<pin_id>\d+)'
    _rPinName   = r'(?P<pin_name>[^\s]+)'
    _rPadId     = r'Pad:\s+(?P<pad_id>\d+)'
    _rClassId   = r'Class:\s+(?P<class_id>\d+)'
    _rBlockName = r'(?P<block_name>[^\s]+)'
    _rBlockId   = r'\(#(?P<block_id>\d+)\)'
    _rPinClassId= r'Pin class\s+(?P<pin_class_id>\d+)'

    # Common start of lines
    _rNet       = r'Net\s+'+_rNetId+r'\s+'+_rEndpoint+r'$'
    _rGlobalNet = r'Net\s+'+_rNetId+r'\s+'+_rEndpoint+r': global net connecting:'
    _rBlock     = r'Block\s+'+_rBlockName+r'\s+'+_rBlockId
    _rChanX     = r'Node:\s+'+_rNodeId+r'\s+CHANX\s+'+_rCoords
    _rChanY     = r'Node:\s+'+_rNodeId+r'\s+CHANY\s+'+_rCoords
    _rInPin     = r'Node:\s+'+_rNodeId+r'\s+IPIN\s+'+_rCoords
    _rOutPin    = r'Node:\s+'+_rNodeId+r'\s+OPIN\s+'+_rCoords
    _rSink      = r'Node:\s+'+_rNodeId+r'\s+SINK\s+'+_rCoords
    _rSource    = r'Node:\s+'+_rNodeId+r'\s+SOURCE\s+'+_rCoords

    # All regex to parse routing segment structures
    _rcNet      = re.compile(_rNet)
    _rcGlobalNet= re.compile(_rGlobalNet)
    _rcBlock    = re.compile(_rBlock+r'\s+at\s+'+_rCoords+r',\s+'+_rPinClassId)
    _rcChanX    = re.compile(_rChanX+r'\s+'+_rTracks+r'\s+'+_rSwitchId)
    _rcChanX2   = re.compile(_rChanX+r'\s+'+_rTrack+r'\s+'+_rSwitchId)
    _rcChanXTo  = re.compile(_rChanX+r'\s+'+_rCoordsTo+r'\s+'+_rTracks+r'\s+'+_rSwitchId)
    _rcChanXTo2 = re.compile(_rChanX+r'\s+'+_rCoordsTo+r'\s+'+_rTrack+r'\s+'+_rSwitchId)
    _rcChanY    = re.compile(_rChanY+r'\s+'+_rTracks+r'\s+'+_rSwitchId)
    _rcChanY2   = re.compile(_rChanY+r'\s+'+_rTrack+r'\s+'+_rSwitchId)
    _rcChanYTo  = re.compile(_rChanY+r'\s+'+_rCoordsTo+r'\s+'+_rTracks+r'\s+'+_rSwitchId)
    _rcChanYTo2 = re.compile(_rChanY+r'\s+'+_rCoordsTo+r'\s+'+_rTrack+r'\s+'+_rSwitchId)
    _rcInPin    = re.compile(_rInPin+r'\s+'+_rPinId+r'\s+'+_rPinName+r'\s+'+_rSwitchId)
    _rcInPad    = re.compile(_rInPin+r'\s+'+_rPadId+r'\s+'+_rSwitchId)
    _rcOutPin   = re.compile(_rOutPin+r'\s+'+_rPinId+r'\s+'+_rPinName+r'\s+'+_rSwitchId)
    _rcOutPad   = re.compile(_rOutPin+r'\s+'+_rPadId+r'\s+'+_rSwitchId)
    _rcSink     = re.compile(_rSink+r'\s+'+_rClassId+r'\s+'+_rSwitchId)
    _rcSinkTo   = re.compile(_rSink+r'\s+'+_rCoordsTo+r'\s+'+_rClassId+r'\s+'+_rSwitchId)
    _rcSinkPad  = re.compile(_rSink+r'\s+'+_rPadId+r'\s+'+_rSwitchId)
    _rcSource   = re.compile(_rSource+r'\s+'+_rClassId+r'\s+'+_rSwitchId)
    _rcSourceTo = re.compile(_rSource+r'\s+'+_rCoordsTo+r'\s+'+_rClassId+r'\s+'+_rSwitchId)
    _rcSourcePad= re.compile(_rSource+r'\s+'+_rPadId+r'\s+'+_rSwitchId)

    # Post-casting format of regex results
    _regex_post_fmt = {
        'net_id'        : int,
        'endpoint'      : str,
        'node_id'       : int,
        'x'             : int,
        'y'             : int,
        'to_x'          : int,
        'to_y'          : int,
        'track'         : int,
        'tracks'        : str,
        'switch_id'     : int,
        'pin_id'        : int,
        'pin_name'      : str,
        'pad_id'        : int,
        'class_id'      : int,
        'block_name'    : str,
        'block_id'      : int,
        'pin_class_id'  : int,
    }

    # Key renaming for each node according to their regex
    _node_list = [
        (_rcChanX,      'chanx'),
        (_rcChanX2,     'chanx'),
        (_rcChanXTo,    'chanx'),
        (_rcChanXTo2,   'chanx'),
        (_rcChanY,      'chany'),
        (_rcChanY2,     'chany'),
        (_rcChanYTo,    'chany'),
        (_rcChanYTo2,   'chany'),
        (_rcInPin,      'ipin'),
        (_rcInPad,      'ipad'),
        (_rcOutPin,     'opin'),
        (_rcOutPad,     'opad'),
        (_rcSink,       'sink'),
        (_rcSinkTo,     'sink'),
        (_rcSinkPad,    'sink'),
        (_rcSource,     'source'),
        (_rcSourceTo,   'source'),
        (_rcSourcePad,  'source'),
    ]

    # Key of each Block
    _block_list = [
        (_rcBlock,     'block'),
    ]

    def __init__(self, filename):
        self.filename   = filename
        self.place_file = ""
        self.array_size = (None, None)
        self._net_ids   = {} # get the corresponding net ID
        self._gnet_ids  = {} # get the corresponding global net ID
        self._nets      = {} # store all nets by ID
        self._gnets     = {} # store all global nets by ID
        self.parse()

    def _format_group(self, groupdict):
        """Format all value in the regex groupdict using the defined rules."""
        assert isinstance(groupdict, dict), "Must be a dictionary type"
        new_groupdict = {}
        for key, val in groupdict.items():
            fmt = str
            if key in self._regex_post_fmt:
                fmt = self._regex_post_fmt[key]
            new_groupdict[key] = fmt(val)
        return new_groupdict

    def _get_net(self, net_id_or_name, nets, net_ids):
        """Intermediate method to search the net."""
        # for the net id search
        if isinstance(net_id_or_name, int):
            if net_id_or_name in nets:
                return nets[net_id_or_name]
        # for the net name search
        if isinstance(net_id_or_name, str):
            if net_id_or_name in net_ids:
                return nets[net_ids[net_id_or_name]]
        return None

    def parse(self):
        """Parse the route file using the regex class."""
        with open(self.filename, 'r') as fp:
            net, gnet = None, None
            for line in fp.readlines():
                line = line.rstrip()
                # file information
                m = self._rcPlaceFile.match(line)
                if m:
                    self.place_file = m.group(1)
                    continue
                m = self._rcArraySize.match(line)
                if m:
                    self.array_size = (int(m.group(1)), int(m.group(2)))
                    continue
                # ignore empty line
                if len(line) == 0:
                    continue
                # Net header
                m = self._rcNet.match(line)
                if m:
                    # add the last net to the database of nets
                    if net is not None:
                        self._nets[net.id]          = net
                        self._net_ids[net.endpoint] = net.id
                    # create a new net object
                    net = Net(**self._format_group(m.groupdict()))
                    continue
                # Global Net header
                m = self._rcGlobalNet.match(line)
                if m:
                    if gnet is not None:
                        self._gnets[gnet.id]          = gnet
                        self._gnet_ids[gnet.endpoint] = gnet.id
                    gnet = Net(**self._format_group(m.groupdict()))
                    continue
                # prevent from file header
                if net is None and gnet is None:
                    continue
                # add a node to the current net object
                is_net = False
                for regex, key in self._node_list:
                    m = regex.match(line)
                    if m:
                        is_net = True
                        node = self._format_group(m.groupdict())
                        node['node_type'] = key
                        net.append(node)
                        break
                if is_net:
                    continue
                # add a block to the global
                is_gnet = False
                for regex, key in self._block_list:
                    m = regex.match(line)
                    if m:
                        is_gnet = True
                        gnet.append(self._format_group(m.groupdict()))
                        break
                if is_gnet:
                    continue
                # FIXME: just a quick warning to specify a regex mismatch
                print(f"[-] Warning missing regex for:{line}")
            # do not forget to add the latest net id
            if net is not None:
                self._nets[net.id]              = net
                self._net_ids[net.endpoint]     = net.id
            if gnet is not None:
                self._gnets[gnet.id]            = gnet
                self._gnet_ids[gnet.endpoint]   = gnet.id

    def get_net(self, net_id_or_name):
        """Return the net object using the id or the endpoint."""
        return self._get_net(net_id_or_name, self._nets, self._net_ids)

    def get_global_net(self, net_id_or_name):
        """Return the global net object using the id or the endpoint."""
        return self._get_net(net_id_or_name, self._gnets, self._gnet_ids)

    def print_net(self, net_id_or_name):
        """Print basic info for debugging purpose."""
        net = self.get_net(net_id_or_name)
        for node in net:
            if not 'pin_name' in node:
                node['pin_name'] = ""
            if not 'to_x' in node:
                node['to_x'] = node['x']
            if not 'to_y' in node:
                node['to_y'] = node['y']
            print("{node_id:8} | {node_type:6} | ({x:2},{y:2}) | ({to_x:2},{to_y:2}) | {pin_name}".format(**node))


## Quick and dirty unit test
if __name__ == "__main__":
    import argparse
    from pprint import pprint

    # Parse all arguments
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('route_filename', type=str,
                    help="VPR route file to parse")
    ap.add_argument('-d', '--debug', action='store_true',
                    help="print debugging information")
    ap.add_argument('--net-id', type=int,
                    help="print a net using its id reference")
    ap.add_argument('--net-name', type=str,
                    help="print a net using its endpoint reference")
    args = ap.parse_args()

    rpt = VprRouteParser(args.route_filename)
    rpt.parse()
    if args.net_id:
        rpt.print_net(args.net_id)
    elif args.net_name:
        rpt.print_net(args.net_name)
    else:
        rpt.print_net(0)

