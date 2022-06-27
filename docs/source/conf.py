# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import docutils
import os, sys

# For converting SVG to PNG using rsvg
import sphinxcontrib.rsvgconverter

# For relative module imports
sys.path.append(os.path.abspath("../../platform"))
sys.path.append(os.path.abspath("../../platform/tools"))

# For readthedocs online compilation to pass
os.environ['OPENFPGA_PATH'] = os.path.abspath("../../third_party/OpenFPGA")

# -- Project information -----------------------------------------------------

project = u'OpenFPGA-Softcores'
copyright = u'2022, LNIS'
author = u'LNIS - University of Utah'

release = u'1.0'
version = u'1.0.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.duration',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinxcontrib.rsvgconverter',
]

# intersphinx options, add reference to the Python3 documentation
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

# napoleon options
napoleon_use_ivar = True
napoleon_use_rtype = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ['.rst']

# The master toctree document.
master_doc = 'index'

# Number figures for referencing
numfig = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# -- Options for Latex output ------------------------------------------------

# -- Options for EPUB output -------------------------------------------------

epub_show_urls = 'footnote'
