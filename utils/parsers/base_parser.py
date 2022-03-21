#!/usr/bin/env python3

import os, sys, re
from glob import glob
from collections import OrderedDict

class BaseParser(object):
    """
    Generic class used to parse any loggers, reports or results file, only
    using regular expression and tokens.
    """
    def __init__(self, filename, searchdir=None, section=None):
        # if basedir is defined, automatically locate the file path
        if searchdir is not None:
            filenames = glob(f"{searchdir}/**/{filename}", recursive=True)
            if len(filenames) != 1:
                print(f"Warning: '{filename}' not found in '{searchdir}'!")
            else:
                filename = filenames[0]
        # define a defautl section name for debugging
        if section is None:
            section = type(self).__name__
        self.section        = section
        # save the full filename path and the search dir
        self.filename       = filename
        self.searchdir      = searchdir
        # save all parsed results in a dictionary
        self.results        = OrderedDict()
        # keep each regex rules in a dictionary
        self._regex_rules   = []
        self._mregex_rules  = []

    def __str__(self):
        """Print the content of the results attribute using th INI format."""
        results = '\n'.join([f"{k} = {v}" for k, v in self.results.items()])
        return f"[{self.section.upper()}]\n{results}"

    def add_regex_rule(self, regex, keyname):
        """
        Catch the first group of the regex and store it in the 'results'
        attribute according to its associated key. All rules are saved and
        called during the 'parse' method is executed.
        """
        self._regex_rules.append({
            'key'   : keyname,
            'regex' : regex,
        })

    def add_multiline_regex_rule(self, start_trig, end_trig, regex, keyname):
        """
        Catch a block of data, located between the 'start' trigger and the
        'end' trigger. All results are saved with the 'keyname' as prefix and
        the first group of the regex, and the value corresponds to the second
        group of the regex. These catches are performed when the 'parse'
        method is executed.
        """
        self._mregex_rules.append({
                'key'   : keyname,
                'start' : start_trig,
                'end'   : end_trig,
                'regex' : regex,
                'token' : False,
        })

    def parse(self):
        """
        Parse the 'filename' line per line for each single and multiple line
        regular expressions. Tokens are used for the multiline regex strategy,
        triggered by the 'start' and 'end' associated regex.
        """
        # test if the file exist
        if not os.path.isfile(self.filename):
            print(f"Warning: '{self.filename}' not found!")
            return
        # parse the file
        with open(self.filename, 'r') as fp:
            for line in fp.readlines():
                line = line.rstrip()
                # single line regex parsing
                for rule in self._regex_rules:
                    m = re.search(rule['regex'], line)
                    if m:
                        self.results[rule['key']] = m.group(1)
                # multiline regex parsing
                for rule in self._mregex_rules:
                    # end trigger
                    if rule['token'] is True and re.search(rule['end'],line):
                        rule['token'] = False
                    # catch the multiline contents
                    m = re.search(rule['regex'], line)
                    if m and rule['token']:
                        self.results[f"{rule['key']}.{m.group(1)}"] = m.group(2)
                    # start trigger
                    if rule['token'] is False and re.search(rule['start'],line):
                        rule['token'] = True

