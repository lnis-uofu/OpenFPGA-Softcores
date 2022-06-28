Getting Started
===============

Installation
------------

Option A - Standalone Install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This option should be used for a standalone installation, when `OpenFPGA`_ is not installed.
These following commands will checkout the latest version of the `OpenFPGA-Softcores` platform and its submodules (`OpenFPGA`_, `PicoRV32`_, `Ibex`_, `VexRiscv`_, ...), install `OpenFPGA` framework and source the project environment.

.. code-block:: bash
   
   git clone --recursive https://github.com/lnis-uofu/OpenFPGA-Softcores.git
   cd OpenFPGA-Softcores
   third_party/install_openfpga.sh                  # install OpenFPGA framework
   source setup_env.sh                              # source the project environment

.. note::

   To install `OpenFPGA` make you have the following dependencies installed, as requested here: `OpenFPGA - How to Compile`_

Option B - Link OpenFPGA
~~~~~~~~~~~~~~~~~~~~~~~~

This option used external `OpenFPGA`_ framework installation, but still install soft-core submodule dependencies.

.. code-block:: bash
   
   git clone https://github.com/lnis-uofu/OpenFPGA-Softcores.git
   cd OpenFPGA-Softcores
   git submodule update --init --recursive third_party/softcores
   export OPENFPGA_PATH="<OPENFPGA_INSTALL_PATH>"   # specify the OpenFPGA install path
   source setup_env.sh                              # source the project environment

.. note::
   
   Before using `OpenFPGA-Softcores` tools, please export the ``OPENFPGA_PATH`` environment variable to used architectures, scripts and tools provided by the `OpenFPGA` framework.

Dependencies
~~~~~~~~~~~~

To install all Python packages required by both *OpenFPGA* framework and *OpenFPGA-Softcores* project, execute the following commands either on your own machine or in a virtual Python environment.

.. code-block:: bash

   pip install -r requirements.txt                  # to support OpenFPGA-Softcores scripts
   pip install -r $OPENFPGA_PATH/requirements.txt   # to support OpenFPGA scripts
   pip install -r docs/requirements.txt             # only for developers


.. note::
   
   Currently Python 3.6 is supported.

Virtual Python Environment
--------------------------

If you are in a restricted environment without admin rights, you can install a virtual Python environment.
Execute the following commands to add the ``pyvenv`` directory in the root of the project, then execute the list of commands described in the previous `Dependencies` section.

.. code-block:: bash

   python3 -m venv pyvenv                                 # create a virtual env
   source pyvenv/bin/activate                             # active virtual env (bash/zsh)
   pip install --upgrade pip                              # upgrade Pip

If you have admin rights, you can still install a virtual Python environment according to operating system.
This is currently working on Linux/MacOS operating systems.

Ubuntu (>=18.04)
~~~~~~~~~~~~~~~~

Open up a terminal and enter the following command sequence.

.. code-block:: bash

   python3 --version                                      # check for Python >3.6
   sudo apt update                                        # update package information
   sudo apt install python3-dev python3-pip python3-venv  # install dependencies
   python3 -m venv pyvenv                                 # create a virtual env
   source pyvenv/bin/activate                             # active virtual env (bash/zsh)
   pip install --upgrade pip                              # upgrade Pip

macOS (>=10.15)
~~~~~~~~~~~~~~~

Open up a terminal and enter the following command sequence.

.. code-block:: bash

   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   export PATH="/usr/local/opt/python/libexec/bin:$PATH"
   brew update
   brew install python
   python3 --version                                      # check for Python 3.6 - 3.10
   python3 -m venv pyvenv                                 # create a virtual env
   source pyvenv/bin/activate                             # active virtual env
   pip install --upgrade pip                              # upgrade Pip

.. warning::

   Currently, the *OpenFPGA* framework is only supported for the ``Ubuntu >=18.04`` and ``Red Hat >=7.5`` platforms.


.. _openfpga: https://github.com/lnis-uofu/OpenFPGA
.. _openfpga - how to compile: https://openfpga.readthedocs.io/en/master/tutorials/getting_started/compile/
.. _vexriscv: https://github.com/SpinalHDL/VexRiscv
.. _picorv32: https://github.com/YosysHQ/picorv32
.. _ibex: https://github.com/lowRISC/ibex
