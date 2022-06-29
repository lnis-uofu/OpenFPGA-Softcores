Analysis
========

.. note::

   This section is still in development to provide generic scripts.
   However, current PicoRV32 analysis demonstrate a proof-of-concept of what results to achieve.

Multiple Task Launchers
-----------------------

You can find different launchers using the plaform in the ``examples/`` directory.
They are using the ``--run-tests`` argument of the ``run-softcore`` tool to execute a loop of tests with various design parameters.
Then, the same test file is used as the ``param-file`` option in the following tools to align the inputs and the results.
   
``analyze-yosys-vpr``
---------------------
.. program:: analyze-yosys-vpr

Basic Usage
~~~~~~~~~~~

This tool provides a quick data analysis coming from the *Yosys* and *VPR* generated files.

.. code-block:: bash

   analyze-yosys-vpr <yosys-vpr-result-file>

Optional Arguments
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   --param-file <file>  Name of the parameter file to label the data
   
   -x <column>, --x-axis <column>
                        Column name to be printed on the X-axis
                        (default: vpr.critical_path)
                        
   -y <column>, --y-axis <column>
                        Column name to be printed on the Y-axis
                        (default: vpr.channel_width)
                        
   -l <column>, --labels <column>
                        Column name to be printed with labels
                        (default: params.memory_size)
                        
   --annotate           Annotate with point with labels
                        (default: False)

   --legend             Add the legend on the figure
                        (default: False)

   --fig-size <width>x<height>
                        Figure dimensions
                        (default: 5x5)

   -o <file>, --output <file>
                        Directory to save the generated figure
                        (default: figures/yosys_vpr.pdf)

``analyze-placing``
-------------------
.. program:: analyze-placing

Basic Usage
~~~~~~~~~~~

This tool provides a post-route path analysis by grouping every paths by *Physiscal Block* (PB) types (*ff*, *bram*, *io*) or by bus names related to the RTL description of the soft-core.

.. code-block:: bash

   analyze-placing <search-path> <param-file>

Optional Arguments
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   -s <name>, --softcore <name>
                        Name of the soft-core design to evaluate (only used for printing)
                        (default: PicoRV32)

   --fig-size <width>x<height>
                        Figure dimensions
                        (default: 8x5)

   --fig-format {pdf,png,svg}
                        Figure file format
                        (default: pdf)

   -o <path>, --output-dir <path>
                        Directory to save the generated figures
                        (default: figures)
                        
   --nb-bus <int>       Number of group of path (buses) to display
                        (default: 10)
   
   --nb-worst <int>     Number of critical path to display
                        (default: 10)
   
   --bus-type           Print by bus types rather than PB types
                        (default: False)
   
   --hide-ff2ff         Hide FF to FF paths
                        (default: True)

