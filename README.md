# OpenFPGA-Softcores

The goal of the project is to co-architect 32-bit open-source RISC-V soft-cores according to given architectural parameters.
Those parameters include BRAM (DFF, OpenRAM) and DSP (Multiplier/Divider) sizing for low- and mid-range RISC-V processors.

| **Name**                                             | **ISA**   | **Language**  | **Stages** | **Interface** | **App Range**   |
|------------------------------------------------------|-----------|---------------|------------|---------------|-----------------|
| [VexRiscv](https://github.com/SpinalHDL/VexRiscv)    | I,M,A     | Scala/Verilog | 2-5        | WB, AXI       | Low/Mid         |
| [PicoRV32](https://github.com/YosysHQ/picorv32)      | I,M,C     | Verilog       | 3          | WB, AXI       | Low (High-Perf) |
| [SERV](https://github.com/olofk/serv)                | I,M       | Verilog       | 33         | -             | Low (Low-Area)  |
| [Taiga](https://gitlab.com/sfu-rcl/Taiga)            | I,M,A     | SystemVerilog | 3          | WB            | Low             |
| [Ibex](https://github.com/lowRISC/ibex)              | I,M,C,E,B | SystemVerilog | 2          | -             | Low             |
| [RISCY](https://github.com/pulp-platform/pulpissimo) | I,M,C,F   | SystemVerilog | 4          | -             | Mid             |

## Get Started

Install, build and source the latest [OpenFPGA](https://github.com/lnis-uofu/OpenFPGA) framework version:
```bash
git clone https://github.com/lnis-uofu/OpenFPGA.git
cd OpenFPGA
make all
source openfpga.sh
```

Now the `OPENFPGA_PATH` environment variable is set up to run benchmark soft-cores on specific architectures.
Thus, you can run any softcore benchmarks and FPGA architectures with the following commands:
```bash
./run_softcores.py picorv32 fpga_archs/task_k6_frac_N10_40nm.conf --device-layout 40x40 --channel-width 150 --memory-size 2048
```

Optional arguments:
- `--device-layout <WxH>`: define a fixed FPGA layout dimension (default: auto)
- `--channel-width <integer>`: define a fixed FPGA channel width (default: auto)
- `--memory-size <integer>`: define the memory size of the softcore in Bytes (default: 1024)
- `--isa {i,im,imc}`: enable the associated RISC-V ISA extension (default: `i`)
  - `m`: enable the multiplier/divider extension
  - `c`: enable compressed instruction extension

## Reports and results extractions

For parsing Yosys and VPR reports located in the `run_dir` directory, you can run the following commands:
```bash
./report_parser.py run_dir/run* -o k6_n10_report.csv
```

Optional arguments:
- `-o <csv-file>`: save results in CSV format (default: report_parser.csv)

