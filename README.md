# UVM Cookbook

A practical, example-driven UVM cookbook: from a 2-input AND gate to a RISC-V SoC
testbench. Every example compiles and runs, and every checker is proven by a mutant
that it catches.

> Status: under construction. See `ROADMAP.md` for progress.

## Contents (planned)

| # | Example | Main topics |
|---|---|---|
| 00 | AND gate | Agent anatomy, timing config, deadline checks, RTL to GLS |
| 01 | ALU | Constrained random, coverage, reference models |
| 02 | D flip-flop | Clocking blocks, SVA, setup/hold |
| 03 | Counter | Cycle-accurate prediction, stateful random |
| 04 | FSM | State/transition coverage, white-box checks |
| 05 | FIFOs | Multi-agent benches, clock crossing |
| 06 | Synchronizer, deglitcher, SPI, register map | CDC, timing boundaries, protocol VIP, RAL |
| 07 | Peripheral controller (capstone) | Multi-agent env, virtual sequences, coverage closure |
| 08 | Subsystem | Env of envs, vertical reuse |
| 09 | RISC-V SoC | SW-driven tests, scaling a testbench |

## Working on this repository

```bash
tools/setup.sh                    # QC tools (.venv, Verible) and git hooks
python3 tools/step.py status      # where the project stands
python3 tools/qc.py               # tool feedback
```

The process is described in `WORKFLOW.md`.

## Tools

- Reference UVM simulator: Cadence Xcelium (`xrun`).
- Open-source: Verilator, Icarus Verilog, Verible, MkDocs Material.
- UVM: IEEE 1800.2 by default; UVM 1.2 by switch.

## License

To be decided (step P0.6).
