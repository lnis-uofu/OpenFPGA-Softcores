Parsers API
===========

The Parsers API is chapter describes all public classes and methopds to parse OpenFPGA, Yosys and VPR generated files, as presented in :numref:`fig_flow_files`.

.. figure:: ../images/openfpga-softcores-io-files.svg
   :width: 80%
   :align: center
   :name: fig_flow_files
   
   Input and output generated files in the OpenFPGA project.

Yosys Parsers
-------------

blif_parser
^^^^^^^^^^^

.. automodule:: parsers.blif_parser
    :members:

yosys_log_parser
^^^^^^^^^^^^^^^^

.. automodule:: parsers.yosys_log_parser
    :members:

VPR Parsers
-----------
 
vpr_net_parser
^^^^^^^^^^^^^^
 
.. automodule:: parsers.vpr_net_parser
    :members:

vpr_place_parser
^^^^^^^^^^^^^^^^^
 
.. automodule:: parsers.vpr_place_parser
    :members:

vpr_route_parser
^^^^^^^^^^^^^^^^
 
.. automodule:: parsers.vpr_route_parser
    :members:

vpr_report_timing_parser
^^^^^^^^^^^^^^^^^^^^^^^^
 
.. automodule:: parsers.vpr_report_timing_parser
    :members:

vpr_log_parser
^^^^^^^^^^^^^^
 
.. automodule:: parsers.vpr_log_parser
    :members:

