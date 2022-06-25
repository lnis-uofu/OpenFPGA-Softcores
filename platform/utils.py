#!/usr/bin/env python3

from os.path import abspath, dirname, join

class ProjectEnv:
    """
    Base directories, paths and files variables for this project, to facilitate
    absolute file manipulation.
    """
    platform_path       = abspath(dirname(__file__))
    project_path        = abspath(join(platform_path, ".."))
    softcore_path       = abspath(join(platform_path, "softcores"))
    softcore_tmpl_path  = abspath(join(softcore_path, "templates"))
    third_party_path    = abspath(join(project_path, "third_party"))
    softcore_3rd_path   = abspath(join(third_party_path, "softcores"))

