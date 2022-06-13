#!/usr/bin/env python3

import os, re
try:
    # Try for the fast c-based version first
    import xml.etree.cElementTree as ET
except ImportError:
    # Fall back on python implementation
    import xml.etree.ElementTree as ET


def pdebug(text, print_mesg=True, prefix="[DEBUG] ", retval=None):
    """Print a debugging message with the right format and return."""
    if print_mesg:
        print(f"{prefix}{text}")
    return retval


class Block:
    """
    Each block contains the following attributes:
    - `direction`: direction of the signal (input/output)
    - `hierarchy`: instance hierarchy to retrace the signal depth
    - `id`       : block identifier used to locate the block in the VPR grid
    - `name`     : block name used by the post-BLIF design
    - `pin_name` : pin name of the mapped instance
    - `pin_numb` : pin number of the physical block, refering to a bus type
    - `point`    : full startpoint or endpoint name used in the timing report
    - `port_name`: port name of the physical block
    - `type`     : block type (clb, memory, dsp ...)
    """
    def __init__(self, point_name, **kwargs):
        # default parameters
        self.direction  = kwargs.get('direction', "")
        self.hierarchy  = kwargs.get('hierarchy', [])
        self.id         = kwargs.get('id', None)
        self.name       = kwargs.get('name', "")
        self.pin_name   = kwargs.get('pin_name', "")
        self.pin_numb   = kwargs.get('pin_numb', None)
        self.point      = point_name
        self.port_name  = kwargs.get('port_name', "")
        self.type       = kwargs.get('type', "")
        # catch the start/end point string format
        m = re.match(r'(.*)\.([^\.\[]+)\[(\d+)\]', point_name)
        if m:
            self.name       = m.group(1)
            self.port_name  = m.group(2)
            self.pin_numb   = int(m.group(3))


class VprNetParser(object):
    """
    Parse the XML structure describing the mapping of the benchmark design on
    the FPGA architecture target. Since this object is use collaboratively
    with the VPR timing report files, startpoint and endpoint are used to
    retrace the block properties, as defined in the Block object.

    - Startpoints are outputs, listed in the *.place report,
    - Endpoints are inputs, listed in the *.route report.
    """

    def __init__(self, filename, debug=False):
        self.filename   = filename
        self.debug      = debug
        self.tree       = ET.parse(filename)
        self.root       = self.tree.getroot()

    def _find_instance(self, block, parent, hier=[]):
        """
        Recursively find a given block name inside a block object, and return
        the corresponding block, port and pin objects.
        """
        assert isinstance(block, Block), "Wrong 'block' type"
        # for each sub-block
        for subb in parent.findall('block'):
            # add a level of hierachy, if with have block children
            hier.append(subb.attrib['instance'])
            # recursive look-up
            instance = self._find_instance(block, subb, hier)
            if instance:
                return instance
            # remove the last level if the block is not found
            hier.pop()
        # search for the block name
        block_obj = parent.find(f"./block/[@name='{block.name}']")
        if block_obj:
            # search through the various port types
            for port_obj in block_obj:
                pin_obj = port_obj.find(f"./port/[@name='{block.port_name}']")
                # RG: that None condition must be written this way to work
                if pin_obj is not None:
                    return parent, block_obj, port_obj, pin_obj
        return None

    def find_block(self, point_name):
        """
        Return a block structure with the corresponding block info else None.
        """
        block = Block(point_name)
        # try to find the corresponding block object in the hierarchy
        instance = self._find_instance(block, self.root, block.hierarchy)
        if instance is None:
            return pdebug(f"No '{block.name}' found in the hierarchy", self.debug)
        parent_obj, block_obj, port_obj, pin_obj = instance
        # add the direction
        block.direction = port_obj.tag.rstrip('s')
        # add the last instance
        block.hierarchy.append(block_obj.attrib['instance'])
        # add the block ID and the type
        m = re.search(r'([^\[]+)\[(\d+)\]', block.hierarchy[0])
        if m:
            block.type = m.group(1)
            block.id   = int(m.group(2))
        # get the pin name
        # XXX: instance pin names mapped on the physical block are different
        # according to the PB type (clb, dpram, dsp).
        # Memory PB type will map the input signal at the parent block level
        if block.hierarchy[0].startswith("memory") and block.direction.startswith("in"):
             pin_obj = parent_obj.find(f"./inputs/port/[@name='{block.port_name}']")
        # default cases, take the block signals
        if not hasattr(pin_obj, "text"):
            return pdebug(f"Missing text attribute in the pin structure", self.debug)
        pin_list = pin_obj.text.split()
        if block.pin_numb > len(pin_list):
            return pdebug(f"pin number out of bound", self.debug)
        block.pin_name = pin_list[block.pin_numb]
        # CLB PB type will keep the same pin name as the block name
        if block.hierarchy[0].startswith("clb"):
            block.pin_name = block.name
        # return the block object
        return block

    def print_point(self, point_name):
        block = self.find_block(point_name)
        if not block:
            pdebug("Missing block info", self.debug)
            return
        block.hierarchy = '->'.join(block.hierarchy)
        # define the printing format
        line_fmt = "{point:70} | {direction:6} | {id:3} | {hierarchy:45} | {pin_name}"
        print(line_fmt.format(**block.__dict__))


if __name__ == "__main__":
    import argparse

    # Parse all arguments
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('net_filename', type=str,
                    help="VPR net (xml) file to parse")
    ap.add_argument('-d', '--debug', action='store_true',
                    help="print debugging information")
    args = ap.parse_args()

    vnp = VprNetParser(args.net_filename, debug=args.debug)
    # list of start and end points
    # FIXME: basic test with picosoc (BRAM+DSP) to remove afterall
    vnp.print_point("$auto$memory_bram.cc:1005:replace_memory$7212.B[24].data_out[7]")
    vnp.print_point("$abc$136328$aiger136327$2736.in[2]")
    vnp.print_point("$abc$136328$aiger136327$2736.out[0]")
    vnp.print_point("$abc$136328$aiger136327$2739.in[0]")
    vnp.print_point("$abc$136328$aiger136327$2739.out[0]")
    vnp.print_point("$abc$136328$aiger136327$2757.in[0]")
    vnp.print_point("$abc$136328$aiger136327$2757.out[0]")
    vnp.print_point("$abc$136328$aiger136327$2760.in[2]")
    vnp.print_point("$abc$136328$aiger136327$2760.out[0]")
    vnp.print_point("cpu.mem_rdata_latched[0].in[4]")
    vnp.print_point("cpu.mem_rdata_latched[0].out[0]")
    vnp.print_point("$abc$136328$aiger136327$3465.in[0]")
    vnp.print_point("$abc$136328$aiger136327$3465.out[0]")
    vnp.print_point("$abc$136328$aiger136327$4013.in[0]")
    vnp.print_point("$abc$136328$aiger136327$4013.out[0]")
    vnp.print_point("$abc$136328$flatten\cpu.$0\decoded_rs1[4:0][3].in[0]")
    vnp.print_point("$abc$136328$flatten\cpu.$0\decoded_rs1[4:0][3].out[0]")
    vnp.print_point("$abc$136328$auto$mem.cc:1149:emulate_transparency$6488[0].raddr[6]")
    vnp.print_point("$techmap5610$flatten\cpu.\genblk1.pcpi_mul.$mul$./benchmark/picorv32.v:2366$857.Y[0].A[1]")
    vnp.print_point("$techmap5610$flatten\cpu.\genblk1.pcpi_mul.$mul$./benchmark/picorv32.v:2366$857.Y[0].Y[60]")

