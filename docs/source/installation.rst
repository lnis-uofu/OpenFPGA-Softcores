Installation
============

Python
------

Before installing the OpenFPGA-Softcores platform you will need to set up a Python environment.

.. note::
   Currently Python 3.6 is supported.

Ubuntu (>=18.04)
^^^^^^^^^^^^^^^^
Open up a terminal and enter the following command sequence.

.. code-block:: bash

   python3 --version                                      # check for Python 3.6 - 3.10
   sudo apt update                                        # update package information
   sudo apt install python3-dev python3-pip python3-venv  # install dependencies
   python3 -m venv py-venv                                # create a virtual env
   source py-venv/bin/activate                            # active virtual env (bash/zsh)

OpenFPGA-Softcores
------------------

Checkout the current repository, download the associated submodules (OpenFPGA framework, soft-cores, ...).
It highly encouraged to use this method to avoid the tedious work of re-writing your own ``setup_env.sh`` file.

.. code-block:: shell
   
   git clone --recursive https://github.com/lnis-uofu/OpenFPGA-Softcores.git
   cd OpenFPGA-Softcores
   source setup_env.sh


Dependencies
------------

