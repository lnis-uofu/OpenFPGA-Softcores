#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, re, shutil
from glob import glob
from xml.etree import ElementTree

# Check if the OPENFPGA_PATH environment variable exist
if not os.environ.get('OPENFPGA_PATH', None):
    raise RuntimeError("Please source 'openfpga.sh' script in the OpenFPGA github repo first!")

# Architecture directory
OPENFPGA_PATH = os.environ['OPENFPGA_PATH']
VPR_ARCH_PATH = f"{OPENFPGA_PATH}/openfpga_flow/vpr_arch"

class VprArchReader(object):
    """
    Top level names: <models>, <tiles>, <layouts>, <device>, <switchlist>,
    <segmentlist>, <directlist>, <complexblocklist>
    """
    def __init__(self, filename, **kwargs):
        self.filename = filename
        self.root     = ElementTree.parse(filename).getroot()

    def _tostring(self, obj, tablevel=0, space='  '):
        text = ElementTree.tostring(obj, encoding='utf-8').decode('utf-8')
        return space*tablevel + re.sub('\n\s*\n', '\n', text.rstrip())

    def _compare_elements(self, elem1, elem2):
        # test tag
        if elem1.tag != elem2.tag:
            return False
        # test attrib
        for key, value in elem1.attrib.items():
            if not key in elem2.attrib:
                return False
            if elem2.attrib[key] != value:
                return False
        # test text
        if elem1.text and elem2.text:
            if elem1.text.strip() != elem2.text.strip():
                return False
        # test children
        children1, children2 = elem1.getchildren(), elem2.getchildren()
        if len(children1) != len(children2):
            return False
        if len(children1) == 0:
            return True
        # test list
        for child1, child2 in zip(children1, children2):
            if self._compare_elements(child1, child2) is False:
                return False
        return True

    def save_level(self, level_name="models", tablevel=2, space='  '):
        # check existing level name
        if not self.root.find(level_name):
            print(f"Missing top level name: '{level_name}'")
            return
        # check if the folder exist
        if not os.path.isdir(level_name):
            os.makedirs(level_name)
        # for each item in the current level
        for item in self.root.find(level_name):
            # fix 'device' level weird structure
            if 'name' in item.attrib:
                item_name = item.attrib['name']
            else:
                item_name = item.tag
            filename = f"{level_name}/{item_name}.xml"
            # prevent double items
            if os.path.isfile(filename):
                saved = ElementTree.parse(filename).getroot()
                exist = False
                for node in saved:
                    if self._compare_elements(item, node):
                        exist = True; break
                if not exist:
                    saved.append(item)
                    # fix last bad space indent
                    for i in saved:
                        i.tail = "\n" + space*tablevel
                    saved[-1].tail = '\n'
                    # save the new list of items
                    with open(filename, 'w') as fp:
                        fp.write(self._tostring(saved))
            else:
                # save the new item in the corresponding file
                with open(filename, 'w') as fp:
                    itemstr = self._tostring(item, tablevel, space)
                    fp.write(f"<{level_name}>\n{itemstr}\n</{level_name}>")

    def save_all_levels(self):
        for level in self.root:
            self.save_level(level.tag)

# for each VPR architectures
for arch_file in glob(f"{VPR_ARCH_PATH}/*.xml"):
    print(f"[+] {arch_file.split('/')[-1]}")
    vpr = VprArchReader(arch_file)
    vpr.save_all_levels()
