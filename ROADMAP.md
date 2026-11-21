# Roadmap

Detailed, step-by-step plan. The vision and the strategy tables are in `PLAN.md`. How a
step is executed is in `WORKFLOW.md`. Live status: `python3 tools/step.py status`.

Each step is one pass through the loop and one commit. A step lists its **deliverables**
and its **gates** (what must be true for PASS). Step files live in `steps/<ID>.md`.

## Decisions (agreed 2026-11-21)

| # | Decision |
|---|---|
| D-01 | Independent project. All examples live in this repository; nothing is pulled from `uvm-testbench`. Code may be ported from there, then owned here. |
| D-02 | UVM IEEE 1800.2 is the default (`UVM=ieee`). A switch selects legacy UVM 1.2 (`UVM=1.2`). Code that differs is guarded and documented. |
| D-03 | Simulators: Xcelium (`xrun`) and open-source tools only. |
| D-04 | Public repository and site. No machine paths, license paths, or personal data in committed files. |
| D-05 | The capstone (07) is a whole independent example with its own RTL copies. |
| D-06 | Bus: APB for registers (06d, 07), AXI-lite for subsystem and SoC (08, 09). To be refined. |
| D-07 | SoC uses a small open RISC-V core running C tests. Candidate: PicoRV32 (ISC license, plain Verilog). Decided in P7.1. |

## Environment facts (checked 2026-11-21)

| Tool | State | Use |
|---|---|---|
| Xcelium 20.09 (`xrun`) | Installed (not on default PATH); ships `CDNS-IEEE`, `CDNS-1.2` | Reference UVM simulator |
| Verilator 5.032 | Installed; cannot compile UVM | RTL lint, RTL-only smoke |
| Icarus Verilog | Installed; no UVM | RTL-only smoke |
| `riscv64-unknown-elf-gcc` | Installed (can target rv32) | SoC firmware |
| Yosys | Not installed | GLS netlists (P1.8) |
| Verible, MkDocs, codespell, yamllint | Installed by `tools/setup.sh` | QC |

Known xrun issue (from the uvm-testbench work): a passing run can exit with code 1 due to
`*E,IMPDLL`. Pass/fail is decided from the UVM report summary and the pass-criteria line,
never from the exit code. Fixed or worked around in P0.3.

## Standard sub-steps for an example (E.1 to E.9)

Every example from 01 onward is built with the same sub-steps. A phase lists them as
`Pn.k: <example> E.x`.

| Sub-step | Content | Gate |
|---|---|---|
| E.1 Spec | `docs/spec.md`: behavior, timing table, checker registry (IDs), coverage plan, mutants, pass criteria | Human review |
| E.2 RTL + mutants | `design/rtl/`, `dv/mutants/` (one per planned checker) | Verilator lint clean |
| E.3 Agent(s) | interface, item, cfg, sequencer, driver, monitor, agent | Compiles on xrun (both UVM versions) |
| E.4 Env + checkers | predictor, scoreboard, timing checker, SVA | Compiles |
| E.5 Stimulus + tests + top | base seq, targeted seqs, base test, top, run files | Golden run passes the arithmetic pass criteria |
| E.6 Coverage | covergroups, assertion cover | Coverage goals in spec met |
| E.7 Mutant proof | mutant regression | Every mutant killed; kill table generated |
| E.8 Chapter page | page from the template, snippets from real files | `mkdocs build --strict` |
| E.9 Recipes | recipe pages extracted from this example | Each recipe links to the example |

---

## Phase 0: Foundation

| ID | Step | Deliverables | Gates |
|---|---|---|---|
| P0.1 | Repository, workflow, QC harness | `README.md`, `CLAUDE.md`, `WORKFLOW.md`, `ROADMAP.md`, `PLAN.md`, `tools/step.py`, `tools/qc.py`, `tools/setup.sh`, git hooks, `.gitignore`, step template | `qc.py` runs; hooks refuse a commit without a passed step |
| P0.2 | Site skeleton | `mkdocs.yml` (Material), nav, landing page, example-page and recipe-page templates, snippet-marker convention, glossary stub | `mkdocs build --strict` passes; one page includes a snippet from a real file |
| P0.3 | Simulation flow | `flow/Makefile.common`, `flow/env.sh.example` (local copy git-ignored), `UVM=ieee\|1.2` switch, `SIM=xrun\|verilator\|icarus`, log parser `tools/simlog.py` (pass = summary counts + pass-criteria line), hello-UVM smoke | Smoke passes on xrun with both UVM versions; IMPDLL issue fixed or documented |
| P0.4 | Regression and mutant runner | `regress.yaml` schema, `tools/regress.py`, `tools/mutate.py`, results JSON in `results/` with tool versions and a source hash | A dummy example runs golden + mutant; mutant reported killed |
| P0.5 | Open-source track | Verilator lint rules, RTL-only smoke harness (Icarus/Verilator), evaluation of a newer Verilator for UVM; decision recorded | Lint runs in `qc.py`; decision recorded in the step file |
| P0.6 | Public hygiene and CI | `LICENSE` (to decide: code and docs licenses), `CONTRIBUTING.md`, GitHub Actions running open-source QC + site build, check that committed xrun results match the current source hash | CI green on a branch; stale results detected |
| P0.7 | Style guide | `docs/reference/style.md`: file headers, naming (`i_`/`o_`), package/include rules, report IDs, verbosity policy; `qc.py` enforces headers | Header check covers all `.sv` files |

## Phase 1: Example 00, and_gate (single agent, combinational, timing)

Ported from the uvm-testbench work, then owned here.

| ID | Step | Deliverables | Gates |
|---|---|---|---|
| P1.1 | Spec and architecture | `examples/00_and_gate/docs/spec.md`, `tb_architecture.md` (decisions D1 to D9 carried over) | Human review |
| P1.2 | RTL and mutants | `and_gate.sv`, mutants: OR, NAND, stuck-at-0, X output | Lint clean |
| P1.3 | Agent | if, item, cfg, timing cfg override, sequencer, driver, monitor, agent | Compiles, both UVM versions |
| P1.4 | Env | predictor, obligation scoreboard (deadline + superseding), env | Compiles |
| P1.5 | Stimulus, test, top, run | base seq (directed + random), overlap seq, base test, top, regress.yaml | Golden: `matches + superseded = input changes`; OR mutant killed |
| P1.6 | Value checker and coverage | CHK-X1, covergroup on (a,b) and transitions | X mutant killed; coverage 100% |
| P1.7 | Timing checker (RTL part) | CHK-T2 skew, timing seq, stage gating via `gls_en` | Skew mutant (driver-side) caught |
| P1.8 | GLS | Yosys netlist (or hand netlist with `specify`), SDF, GLS run target; CHK-T1, U1, G1 | Delay-violation mutant (SDF edit) caught |
| P1.9 | Chapter 00 page | page from the template | Strict site build |
| P1.10 | Recipes from 00 | agent anatomy, config layering, obligation scoreboard, timing config, mutant proof, RTL-to-GLS reuse | Each links to chapter 00 |

## Phase 2: Single-agent block benches

| ID | Step | Focus recipes |
|---|---|---|
| P2.1 | 01 ALU: E.1 to E.9 | Constraints (dist, implication, solve-before, soft, inline), policy classes, crosses with illegal bins, parameterized classes, SV vs DPI-C reference model |
| P2.2 | 02 DFF (async reset, enable): E.1 to E.9 | Clocking blocks and skew, clock/reset agent, reset mid-traffic, SVA in interface + `bind`, setup/hold in GLS |
| P2.3 | Promote `clk_rst` VIP to `lib/vip/` | VIP packaging, standalone smoke test, README |
| P2.4 | 03 Counter: E.1 to E.9 | Cycle-accurate predictor, stateful random, long runs, end-of-test drain, assertion coverage |
| P2.5 | 04 FSM: E.1 to E.9 | State/transition coverage, white-box probes, illegal transitions, watchdog, reactive sequences |

## Phase 3: Multi-agent and clock crossing

| ID | Step | Focus recipes |
|---|---|---|
| P3.1 | 05a Sync FIFO: E.1 to E.9 | Producer/consumer agents, in-order scoreboard, backpressure, virtual sequence without sequencer |
| P3.2 | 05b Async FIFO: E.1 to E.9 | Random clock ratios, gray-code pointer checks, CDC introduction |
| P3.3 | 06a Synchronizers (2-FF, pulse, handshake): E.1 to E.9 | Metastability injection model, random phase/jitter, latency windows, pulse-loss checks |
| P3.4 | 06b Deglitcher/debouncer: E.1 to E.9 | Boundary stimulus (N-1, N, N+1), time-based obligations, filter checks |

## Phase 4: Protocols and registers

| ID | Step | Focus recipes |
|---|---|---|
| P4.1 | SPI VIP (master + slave, all CPOL/CPHA) in `lib/vip/spi/` | Protocol VIP structure, reactive slave, protocol SVA, bit timing, error-injection callbacks |
| P4.2 | 06c SPI slave DUT: E.1 to E.9 | Using a VIP from `lib/` in a bench |
| P4.3 | APB VIP in `lib/vip/apb/` | Bus VIP, slave responder |
| P4.4 | 06d Register map: E.1 to E.9 | RAL model, adapter + predictor, frontdoor/backdoor, built-in reg seqs, field policies (RW, RO, W1C, RC), mirror checks |
| P4.5 | (optional) I2C VIP + example | Open-drain, arbitration, clock stretching |

## Phase 5: Capstone 07, peripheral controller (independent example)

| ID | Step | Content |
|---|---|---|
| P5.1 | Spec | Full IP spec: SPI slave -> regmap -> GPIO (sync + deglitch + edge detect) -> timer -> FSM -> IRQ; checker registry; coverage plan |
| P5.2 | RTL | Own copies of the block RTL, integration, mutants per path |
| P5.3 | Env architecture | Agents (SPI, GPIO async, IRQ passive, clk_rst x2), RAL over SPI (adapter), virtual sequencer |
| P5.4 | Logic checkers | Per-path scoreboards, RAL mirror, IRQ set/clear/mask model, FSM checks |
| P5.5 | Timing checkers | Sync latency, deglitch boundaries, SPI pin timing, IRQ latency budget |
| P5.6 | Stimulus library | Reg seqs, GPIO pulse trains, concurrent virtual seqs, error injection (bad frames, glitches, reset during transfer) |
| P5.7 | Coverage closure | Coverage-driven test additions until goals met; closure report |
| P5.8 | Mutant campaign | Kill table for all checkers |
| P5.9 | Chapter + recipes | Multi-agent env, virtual sequences, RAL over a serial bus, coverage closure |

## Phase 6: Subsystem 08

| ID | Step | Content |
|---|---|---|
| P6.1 | AXI-lite VIP | Master, slave, protocol checks |
| P6.2 | Subsystem RTL | Fabric + capstone IP + second IP (e.g. FIFO-based UART) |
| P6.3 | Env of envs | Block envs reused unchanged as sub-envs (agents passive), nested RAL with address maps, config tree |
| P6.4 | Tests, coverage, mutants, chapter | Vertical reuse with zero edits to block envs |

## Phase 7: SoC 09 (RISC-V)

| ID | Step | Content |
|---|---|---|
| P7.1 | Core selection | PicoRV32 vs alternatives (license, size, Verilator/xrun support); decision recorded |
| P7.2 | Firmware flow | rv32 build with `riscv64-unknown-elf-gcc`, linker script, crt0, hex load, `printf` via mailbox |
| P7.3 | SoC RTL | Core + memory + AXI-lite fabric + subsystem IPs + interrupt routing |
| P7.4 | SoC env | VIPs at the pins, passive block checkers, C-to-UVM sync (mailbox + events), end-of-test from firmware |
| P7.5 | System tests | Boot, register access from C, interrupts, concurrent IO, performance/latency checks |
| P7.6 | Scaling housekeeping | Tiered regressions, compile partitioning, log filtering, triage scripts, coverage merge |
| P7.7 | Chapter + recipes | SW-driven verification, SoC housekeeping |

## Phase 8: Strategy selector and completeness

| ID | Step | Content |
|---|---|---|
| P8.1 | Strategy page | Matrices (architecture, stimulus, checkers, timing, housekeeping) per level, linked to examples |
| P8.2 | Questionnaire | Static JS on the site: answers -> recommended pattern + links |
| P8.3 | Scenario matrix generator | `tools/matrix.py`: recipes x examples from page metadata; gaps listed |
| P8.4 | Gap closure | Recipes without an example get one |

## Phase 9: Release

| ID | Step | Content |
|---|---|---|
| P9.1 | Review pass | Full read-through, broken links, consistency |
| P9.2 | v1.0 | Tag, publish site, release notes |
