#!/usr/bin/env python3

"""
This Python library parses a *Berkeley Logic Interchange Format* (BLIF) and
*Extended BLIF* (EBLIF) files, and generate a Python object for convenient
use. A BLIF file can contain many models and references to models described in
other BLIF files. A model is a flattened hierarchical circuit.
For a detailed description of the BLIF file format, see the
`BLIF documentation <https://www.cs.uic.edu/~jlillis/courses/cs594/spring05/blif.pdf>`_.

In this library, the ``BlifParser`` object is a list of ``BlifModel`` objects.

Examples:
    >>> parser = BlifParser("<blif_filename>")
    >>> model = parser[0]           # get the first model in the file
    >>> model.get_instance("a[0]")  # get the instance name of the point "a[0]"
    >>> model.get_pin("a[0]")       # get the pin name of the point "a[0]"
    >>> model.subckts               # list() type
    >>> model.names                 # dict() type
    >>> model.latches               # dict() type
"""

import os, re, time
import numpy as np
from collections import OrderedDict

class BlifModel(object):
    """Object to store model properties of a design and its hierarchical
    elements. For a given point, it returns the equivalent pin name and the
    instance name used in the Verilog netlist when it is a ``.subckt`` element.

    **Attributes**

    - **name**    (*str*)  -- Name of the BLIF model.
    - **inputs**  (*list*) -- All input signals used by the model.
    - **outputs** (*list*) -- All output signals used by the model.
    - **names**   (*dict*) -- All *logic-gate* (LUT) elements describe in the model.
    - **latches** (*dict*) -- All *generic-latch* elements describe in the model.
    - **subckts** (*list*) -- All *model-reference* elements describe in the model.
    - **conns**   (*dict*) -- All *direct-connection* elements describe in the model.
    """

    def __init__(self, name, **kwargs):
        self.name       = name
        self.inputs     = kwargs.get('inputs', [])
        self.outputs    = kwargs.get('outputs', [])
        self.names      = OrderedDict()
        self.latches    = OrderedDict()
        self.subckts    = list()
        self.conns      = OrderedDict()

    def _split_point(self, point_name):
        """Separate the point name from its pin signal."""
        point = point_name.split('.')
        return '.'.join(point[:-1]), point[-1]

    def _get_pin_subckt(self, subckt, pin_name):
        """Get the subckt pin in the `params` dictionary."""
        for signal, pins in subckt['params'].items():
            for pin in pins:
                if pin == pin_name:
                    return signal
        return None

    def get_pin_names(self, point_name):
        """Get the signal name for a point of a ``.names`` element."""
        output, pin_name = self._split_point(point_name)
        if output in self.names:
            pins = self.names[output]['pins']
            if pin_name in pins:
                return pins[pin_name]
        return None

    def get_pin_latch(self, point_name):
        """Get the signal name for a point of a ``.latch`` element."""
        output, pin_name = self._split_point(point_name)
        if output in self.latches:
            if pin_name in self.latches[output]:
                return self.latches[output][pin_name]
        return None

    def get_pin_subckt(self, point_name):
        """Get the signal name for a point of a ``.subckt`` element."""
        output, pin_name = self._split_point(point_name)
        for subckt in self.subckts:
            if output in subckt['params']:
                return self._get_pin_subckt(subckt, pin_name)
        return None

    def get_pin(self, point_name, element_type=None):
        """Get the pin name of an element.

        The point name is composed of the unique output name and the pin input
        or output of the element.
        Examples of pin name format according to the element type:

        - ``.names``: `in[#]`, `out[#]`
        - ``.latch``: `D[0]`, `Q[0]`
        - ``.subckt``: `data_out[#]`, `data_in[#]`, ...

        Args:
            point_name (str): Point name of element to be found.
            element_type (str, optional): Specific element type to search for
                (`names`, `latch` or `subckt`).
        """
        if element_type in ['names', 'latch', 'subckt']:
            func = getattr(self, f"get_pin_{element_type}")
            return func(point_name)
        for element_type in ['names', 'latch', 'subckt']:
            func = getattr(self, f"get_pin_{element_type}")
            pin_name = func(point_name)
            if pin_name:
                return pin_name
        return None

    def get_instance(self, point_name):
        """Get the Verilog instance name of a ``.subckt`` element.

        .. note::
            Works only when the ``--cname`` option is enabled when Yosys
            generates its output BLIF file with the ``write_blif``
            command.

        Args:
            point_name (str): Point name of the subckt element to be found.
        """
        for subckt in self.subckts:
            if not 'inst' in subckt:
                continue
            output, pin_name = self._split_point(point_name)
            if output in subckt['params']:
                if self._get_pin_subckt(subckt, pin_name):
                    return subckt['inst']
        return None


class BlifParser(object):
    """
    Parse a BLIF/EBLIF file (generated by Yosys) using pre-defined regex
    keywords to create a list of ``BlifModel`` objects, which describe the
    full design. If there is only one model in the BLIF file, then the index
    zero will be used to access it.

    BLIF primitives supported:
    ``.model``, ``.inputs``, ``.outputs``, ``.names``, ``.latch``,
    ``.subckt``, ``.cname``, ``.attr``, ``.conn``

    BLIF primitives not supported:
    ``.cycle``, ``.clock``, ``.clock_event``, ``.area``, ``.delay``,
    ``.start_kiss``, ``.end_kiss``, ``.i``, ``.o``, ``.p``, ``.s``,
    ``.exdc``, ``.mlatch``, ``.latch_order``, ...

    **Attributes**

    - **filename** (*str*)  -- File name of the BLIF/EBLIF file.
    - **models**   (*list*) -- Models described in the BLIF/EBLIF file.
    """

    # Regex to extract BLIF netlist
    _rComment       = r'\s*#(?P<message>.+)'
    _rModel         = r'\.model (?P<name>[^\s#]+)'
    _rInputs        = r'\.inputs (?P<inputs>[^#]+)'
    _rOutputs       = r'\.outputs (?P<outputs>[^#]+)'
    _rLut           = r'\.names (?P<inputs>.+) (?P<output>[^\s#]+)'
    _rLutEq         = r'(?P<inputs>\d+) (?P<output>\d+)'
    _rLatch         = r'\.latch (?P<input>[^\s]+) (?P<output>[^\s]+)\s?((?P<type>[^\s]+) (?P<clk>[^\s]+))?\s?(?P<init>\d+)'
    _rSubckt        = r'\.subckt (?P<name>[^\s]+) (?P<params>[^#]+)'
    _rEnd           = r'\.end' # end of each model

    # Regex to extract EBLIF netlist
    _rCname         = r'\.cname (?P<name>[^\s]+)'
    _rAttr          = r'\.attr (?P<name>[^\s]+) (?P<value>[^\s#]+)'
    _rConn          = r'\.conn (?P<input>[^\s]+) (?P<output>[^\s#]+)'
    _rGate          = r'\.gate (?P<name>[^\s]+) (?P<params>[^#]+)'
    _rParam         = r'\.param (?P<name>[^\s]+) (?P<value>[^\s#]+)'

    # Compiled regexes (for faster parsing)
    _rcComment      = re.compile(_rComment)
    _rcModel        = re.compile(_rModel)
    _rcInputs       = re.compile(_rInputs)
    _rcOutputs      = re.compile(_rOutputs)
    _rcLut          = re.compile(_rLut)
    _rcLutEq        = re.compile(_rLutEq)
    _rcLatch        = re.compile(_rLatch)
    _rcSubckt       = re.compile(_rSubckt)
    _rcEnd          = re.compile(_rEnd)
    _rcCname        = re.compile(_rCname)
    _rcAttr         = re.compile(_rAttr)
    _rcConn         = re.compile(_rConn)

    def __init__(self, filename):
        self.filename   = filename
        self.models     = list()    # list of each model in the file
        self.parse()

    def __str__(self):
        """For debbuging purpose: print(object)."""
        table = []
        for m in self.models:
            table.append(f"model name: {m.name}")
            table.append(f"inputs: {' '.join(m.inputs)}")
            table.append(f"outputs: {' '.join(m.inputs)}")
            for name, lut in m.names.items():
                table.append(f".names {name}")
            for name, latch in m.latches.items():
                src  = latch['src'] if 'src' in latch else None
                table.append(f".latch {name} (src: {src})")
            for subckt in m.subckts:
                name = subckt['name']
                src  = subckt['src'] if 'src' in subckt else None
                inst = subckt['inst'] if 'inst' in subckt else None
                table.append(f".subckt {name} (inst: {inst}, src: {src})")
            for po, pi in m.conns.items():
                table.append(f".conn {po} = {pi}")
        return '\n'.join(table)

    def __len__(self):
        """Return the total number of paths."""
        return len(self.models)

    def __getitem__(self, idx):
        """Use this class as a list, in order to iterate each model."""
        if not self.models:
            return None
        return self.models[idx]

    def parse(self):
        """Parse the BLIF file using the class regex."""
        # Parse the file
        with open(self.filename, 'r') as fp:
            model = None
            block = None
            # read the file line by line
            for line in fp.readlines():
                line = line.rstrip()
                # Just a comment or an empty line
                if len(line) == 0 or self._rcComment.match(line):
                    continue
                # Model object
                m = self._rcModel.match(line)
                if m:
                    model = BlifModel(m.groupdict()['name'])
                if self._rcEnd.match(line):
                    self.models.append(model)
                    model = None
                if model is None:
                    continue
                # Model inputs/outputs
                for attr, regex in zip(['inputs','outputs'],
                                       [self._rcInputs,self._rcOutputs]):
                    m = regex.match(line)
                    if m:
                        io_list = m.groupdict()[attr].strip().split()
                        setattr(model, attr, io_list)
                # LUT block (.names)
                m = self._rcLut.match(line)
                if m:
                    block, pins, m = {}, {}, m.groupdict()
                    for idx, pin in enumerate(m['inputs'].strip().split()):
                        pins[f'in[{idx}]'] = pin
                    pins['out[0]'] = m['output']
                    block['pins'] = pins
                    model.names[m['output']] = block
                # Latch/Flip-Flop block (.latch)
                m = self._rcLatch.match(line)
                if m:
                    block, m = dict(m.groupdict()), m.groupdict()
                    block['D[0]'] = block.pop('input')
                    block['Q[0]'] = block.pop('output')
                    model.latches[m['output']] = block
                # Subckt block (DSP, BRAM) (.subckt)
                m = self._rcSubckt.match(line)
                if m:
                    block, params, m = {}, {}, m.groupdict()
                    for p in m['params'].strip().split():
                        p = p.split('=')
                        # NOTE: VPR don't like single pin name, we need to
                        # change each single pin as a bus-type, such as:
                        # ren -> ren[0]
                        if not "[" in p[0]:
                            p[0] += "[0]"
                        if p[1] in params:
                            params[p[1]].append(p[0])
                        else:
                            params[p[1]] = [p[0]]
                    block['name'] = m['name']
                    block['params'] = params
                    model.subckts.append(block)
                # Conn block (direct wire connection)
                m = self._rcConn.match(line)
                if m:
                    m = m.groupdict()
                    model.conns[m['output']] = m['input']
                # Attributes
                m = self._rcAttr.match(line)
                if m and block is not None:
                    m = m.groupdict()
                    # list of source files
                    if m['name'] == "src":
                        m['value'] = m['value'].strip()[1:-1].split('|')
                    block[m['name']] = m['value']
                # Cname (Verilog instantiation)
                m = self._rcCname.match(line)
                if m and block is not None:
                    m = m.groupdict()
                    block['inst'] = m['name']

    def get_pin(self, point_name, element_type=None):
        """Get the BLIF pin name of a point across all models.

        Args:
            point_name (str): Name of the point to search accross all models.
            element_type (str, optional): Specify the type of the element
                (default is `None`).
        """
        for m in self.models:
            pin = m.get_pin(point_name, element_type)
            if pin is not None:
                return pin
        return None

    def get_instance(self, point_name):
        """Get the Verilog instance name of a point across all *subckt*.

        Args:
            point_name (str): Name of the point to search accross all models.
        """
        for m in self.models:
            inst = m.get_instance(point_name)
            if inst is not None:
                return inst
        return None

## Quick and dirty unit test
if __name__ == "__main__":
    import argparse, sys
    from pprint import pprint

    # Parse all arguments
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('blif_filename', type=str,
                    help="BLIF/EBLIF file to parse")
    ap.add_argument('--point', type=str,
                    help="print the signal name of a given point")
    ap.add_argument('-d', '--debug', action='store_true',
                    help="print the full content of the path list")
    args = ap.parse_args()

    obj = BlifParser(args.blif_filename)
    if not len(obj):
        print(f"[ERROR] no model found in the file: '{args.blif_filename}'")
        sys.exit(0)
    if args.debug:
        print(obj)
        sys.exit(0)
    if args.point:
        print(f"Looking for '{args.point}'")
        for model in obj:
            pin_name  = model.get_pin(args.point)
            inst_name = model.get_instance(args.point)
            print(f"{pin_name} (inst: {inst_name})")
        sys.exit(0)
    # default behavior
    for model in obj:
        if len(model.subckts):
            pprint(model.subckts[0])
        if len(model.names):
            pprint(list(model.names.items())[0])
        if len(model.latches):
            pprint(list(model.latches.items())[0])
