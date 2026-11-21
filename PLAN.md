# UVM Cookbook: Build Plan

Status: agreed vision (2026-11-21). Step-by-step plan: `ROADMAP.md`. Process: `WORKFLOW.md`.
Seed example: the and_gate bench from the uvm-testbench project, ported here in Phase 1.

---

## 1. Goal

An example-driven site that takes an engineer from a 2-input gate to a SoC-level
testbench. Every page is backed by code that compiles and runs. Every checker is proven
by a mutant that it catches.

The site answers three questions for every example:

1. **What to build.** Which components, how they are wired, and why.
2. **How to stimulate it.** Directed, constrained-random, layered, reactive, error injection.
3. **How to know it is right.** Logic checks, timing checks, coverage, and a mutant that
   must fail.

### Principles (taken from the and_gate example)

| # | Principle | Where it comes from in and_gate |
|---|---|---|
| P1 | Spec first. Every checker and cover point has an ID (CHK-F1, CHK-T1) traced to the spec. | `docs/spec.md` 7.2 checker registry |
| P2 | Monitors observe and publish. They hold no limits and make no decisions. | `and_gate_monitor.sv` |
| P3 | Logic checks (scoreboard) and timing checks (timing checker) are separate components, each with an enable flag per stage (RTL, GLS). | Decision D5 |
| P4 | Timing numbers live in one layered config object, never in drivers or monitors. | `and_gate_timing_cfg` extends `and_gate_cfg` (D4) |
| P5 | Checks are driven by obligations with deadlines, not by sampling at arbitrary times. Superseded checks are counted, not dropped. | Scenario H, D8 |
| P6 | The same bench runs on RTL and on GLS with SDF. | Spec section 3 |
| P7 | A testbench is not done until it fails on a mutant. | `dv/mutants/and_gate_or.sv` |
| P8 | Pass criteria are arithmetic, not "no errors": `matches + superseded = input changes`. | Spec section 9 |

These principles become the spine of the site. Each later example repeats them at a
larger scale.

---

## 2. Site structure

```
uvm-cookbook/
  mkdocs.yml                     site config
  docs/                          site pages (Markdown)
    index.md                     landing page + "start here" path
    strategy/                    strategy selector (section 6)
    ladder/                      one chapter per example (section 3)
    recipes/                     cross-cutting recipe tracks (section 4)
    reference/                   glossary, UVM cheat sheets, anti-patterns
  examples/                      real code, one folder per example (section 5 layout)
    00_and_gate/
    01_alu/
    ...
  lib/
    vip/                         promoted, self-contained VIPs (clk_rst, apb, spi, i2c, uart, gpio, irq)
    common/                      shared base classes (obligation scoreboard, report catcher, timing checker base)
  flow/
    Makefile.common              compile/run/cover/mutate targets per simulator
    regress.py                   runs regression lists, collects pass/fail + coverage
    mutate.py                    runs every mutant and checks that it fails
  ci/                            regression + site build
```

### Site tooling (recommended)

- **MkDocs Material.** Code annotations, tabbed code blocks, Mermaid diagrams, search,
  admonitions, dark mode.
- **Snippets from real files** (`pymdownx.snippets` with `// --8<-- [start:name]`
  markers in the `.sv` files). Pages never contain copied code, so the docs cannot drift
  from code that was compiled.
- **Generated results pages.** CI runs the regression and mutants, then writes a results
  table (pass/fail, coverage, mutant kill rate) into each example's page.
- **Simulators.** Xcelium (`xrun`) is the reference UVM simulator. Open-source tools
  (Verilator, Icarus, Verible) cover lint and RTL-only checks, and run in public CI.
  UVM: IEEE 1800.2 by default, UVM 1.2 by switch.

---

## 3. The example ladder

Each rung adds DUT features and the TB concepts they force. Nothing is introduced
before a DUT needs it.

| # | Example | DUT features | TB concepts introduced | TB shape |
|---|---|---|---|---|
| 00 | **and_gate** | Combinational, no clock | Agent anatomy, config layering, input-driven deadline checks, superseding, timing config, RTL/GLS reuse, mutant proof | Single agent |
| 01 | **Parameterized ALU / adder** | Width param, opcodes, carry/overflow | Constraints (dist, solve-before, implication), covergroups with cross and illegal bins, parameterized classes, reference model in SV and in DPI-C | Single agent |
| 02 | **D flip-flop (async reset, enable)** | Clock, reset | Clocking blocks and skew, clock/reset agent, reset mid-traffic, SVA in an interface + `bind`, setup/hold in GLS (`$setup`, `$hold`, notifiers, X-prop) | Single agent + clk_rst agent |
| 03 | **Counter (up/down/load/wrap/saturate)** | Sequential state, parameters | Cycle-accurate predictor, stateful random (history-aware constraints), long-run tests, end-of-test drain, assertion coverage | Single agent + clk_rst |
| 04 | **FSM (handshake controller or sequence detector)** | States, illegal states, timeouts | State and transition coverage, white-box probes via `bind`, illegal-transition checks, watchdog/timeout, reactive sequences | Single agent, white-box monitor |
| 05 | **Sync FIFO, then async FIFO** | Two ports, backpressure, two clocks | Producer/consumer agents, in-order scoreboard, flow control, random clock ratios, CDC introduction | Multi-agent |
| 06a | **Synchronizer (2-FF, pulse, handshake)** | Clock-domain crossing | Metastability injection model, random phase/jitter, latency window checks (min/max cycles), pulse-loss checks | Two clk agents + data agent |
| 06b | **Deglitcher / debouncer** | Filter window | Pulse-width timing stimulus at the boundary (N-1, N, N+1 cycles), glitch-pass/filter checks, time-based obligations | Single agent, timing-heavy |
| 06c | **Serial interface (SPI, I2C or UART)** | Bit-level protocol | Protocol VIP, reactive slave/responder agent, protocol checker (SVA + monitor), bit timing (CPOL/CPHA, baud), error injection via callbacks | Protocol VIP |
| 06d | **Register map** | CSR block, field policies | RAL (`uvm_reg`), adapter + predictor, frontdoor/backdoor, built-in reg sequences, field access policy checks (RW, RO, W1C, RC), mirror checks | Bus agent + RAL |
| 07 | **Capstone IP: peripheral controller** | SPI/I2C slave -> regmap -> (sync + deglitch on GPIO inputs) -> timer/counter -> FSM -> interrupt | Multi-agent env, virtual sequences, RAL over the serial VIP, per-path scoreboards, timing checker per stage, interrupt agent, coverage plan to closure | Multi-agent, virtual seqs |
| 08 | **Subsystem: two IPs + bus fabric (APB or AXI-lite)** | Address decode, shared bus | Vertical reuse (block env becomes sub-env, agents go passive), nested RAL with address maps, config hierarchy, env-of-envs | Env of envs |
| 09 | **SoC-level bench** | Many IPs, clocks, power domains, CPU stub | SW-driven tests (C + UVM via DPI/mailbox), system scenarios, performance/latency checks, interrupt routing, regression at scale, compile partitioning, log/triage | SoC env |

Each rung reuses what the previous rung built. The VIPs created in 02 (clk_rst) and
06c/06d (serial, bus) are promoted to `lib/vip/` and reused in 07 to 09.

### The capstone (07) in more detail

This is where the "complex design with all components" lives:

```
   SPI/I2C pins ──► serial slave ──► register map ──► control/status
                                         │
   GPIO in (async) ──► 2-FF sync ──► deglitcher ──► edge detect ──► IRQ ctrl ──► irq pin
                                         │
                                  timer/counter ──► FSM (watchdog / sequencer)
```

Verification content to demonstrate:

- **Agents:** serial (active master), GPIO (active, async to core clock), irq (passive),
  clk_rst (two domains).
- **Logic checks:** register model mirror, GPIO-to-status path (after sync + deglitch
  latency), interrupt set/clear/mask, FSM transitions.
- **Timing checks:** sync latency min/max, deglitch threshold boundaries, SPI setup/hold
  at pins, interrupt latency budget.
- **Stimulus:** register sequences through RAL, GPIO pulse trains around the filter
  threshold, concurrent traffic via virtual sequences, error injection (bad frames,
  glitches, reset during transfer).
- **Coverage:** register field coverage, GPIO pulse-width bins, interrupt-cause crosses,
  FSM transition coverage.

---

## 4. Cross-cutting recipe tracks

The ladder teaches in order. The recipe tracks are for lookup: "how do I do X".
Each recipe links to the example where it is used for real.

### A. Testbench architecture
- Single-agent bench; active vs passive agents
- Multi-agent bench; when to add a virtual sequencer vs a sequencer-less virtual sequence
- Reactive (responder/slave) agents
- Layered agents (protocol on protocol)
- Env of envs and vertical reuse (block -> IP -> SoC)
- Parameterized agents and interfaces; abstract-class BFM for parameterized interfaces
- VIP packaging and promotion (scenario G in the skill)
- Parallel instances and combined behavior at top level (scenarios D, E)

### B. Stimulus
- Constraint cookbook: `dist`, implication, `solve...before`, `soft`, inline `with`,
  `foreach` on arrays, `unique`, `randc`, `constraint_mode`, `rand_mode`
- Policy classes and constraint layering by inheritance (change distributions per test)
- Stateful random: constraints that depend on history
- Sequence libraries; reusable base sequences with knobs
- Virtual sequences; grab/lock/priority arbitration
- Reactive sequences and response handling
- Error injection with callbacks and factory overrides
- Corner-case and boundary generators (N-1, N, N+1)
- Timing stimulus: pulse widths, skew, jitter, random clock ratios
- Coverage-driven stimulus closure loop

### C. Logic checkers
- Predictor + scoreboard split
- In-order, out-of-order, keyed-by-ID, multi-stream scoreboards
- Obligation/deadline checks with superseding (from and_gate)
- Cycle-accurate vs transaction-level reference models; DPI-C/C++ models
- SVA in interfaces and via `bind`; protocol checkers
- White-box checks (probes into internal state)
- X/Z checks
- End-of-test checks: empty queues, objections, drain time
- Negative tests: expected errors with a report catcher
- Mutation testing to prove a checker works

### D. Timing configuration and checks
- One timing config object, layered over the agent config (D4 pattern)
- Units and `timeunit`/`timeprecision` discipline
- Clocking blocks, input/output skew, race avoidance
- Setup/hold, pulse width, period/jitter checks (in TB and via SDF/specify)
- Latency windows (min/max cycles or ns)
- Timing checker as its own component, stage-gated (RTL vs GLS)
- GLS reuse: SDF annotation, notifiers, X-prop, reset in GLS
- Watchdogs and timeouts

### E. Coverage and verification plan
- Spec -> requirement ID -> checker ID -> cover ID traceability
- Covergroups: bins, crosses, `ignore_bins`, `illegal_bins`, transition bins
- Assertion coverage, RAL coverage
- Coverage merge and closure reports

### F. Configuration and reuse
- Config objects: agent, env, test; layering and overrides
- `uvm_config_db` discipline (who sets, who gets, fatal on missing)
- Factory type and instance overrides
- Runtime switches (`+plusargs`, scenario F)

### G. Housekeeping (scales from gate to SoC)
- Directory layout, naming, file headers (the and_gate header style)
- Packages, includes, filelists
- Makefile targets: compile, run, regress, cover, mutate, gls
- Seeds and reproducibility
- Regression lists (YAML: test, seeds, plusargs, stage)
- Logging: report IDs, verbosity policy, severity overrides, log filtering
- Test status summary and pass criteria arithmetic
- Triage scripts, waivers, CI
- Compile partitioning and run-time at SoC scale

### H. Debug
- Transaction recording, waveform setup
- `+UVM_PHASE_TRACE`, `+UVM_OBJECTION_TRACE`, `+UVM_CONFIG_DB_TRACE`
- Factory and topology prints
- Common failure signatures and what they mean

---

## 5. Standard content per example

Every example uses the and_gate layout so readers learn one shape:

```
NN_<name>/
  docs/
    spec.md              behavior, timing table, checker registry, coverage, mutants, pass criteria
    tb_architecture.md   component-to-file map, data flow, numbered decisions (D1, D2, ...)
  design/rtl/            DUT (zero-delay RTL)
  design/gls/            netlist + SDF (where relevant)
  dv/tb/
    if/  agent/  env/  seqs/  tests/  top/
    <name>_tb_pkg.sv
  dv/mutants/            at least one mutant per checker
  sim/
    Makefile             includes flow/Makefile.common
    regress.yaml         tests, seeds, stages
```

Each **site page** for an example follows one template:

1. **What you will learn** (3 to 5 bullets)
2. **The DUT** (spec excerpt, waveform)
3. **The bench** (Mermaid block diagram; component table)
4. **Walkthrough** (code snippets from the real files, one per component)
5. **Stimulus** (each sequence and what it targets)
6. **Checks** (checker registry: ID, logic or timing, stage, what it catches)
7. **Run it** (command and the expected summary line)
8. **Prove it** (mutant run and the error it produces)
9. **Pitfalls** (what went wrong while building it; the decisions log is the source)
10. **How this scales** (what changes at IP and SoC level)

Each **recipe page** follows: Problem -> When to use -> Code -> Run -> Pitfalls ->
Scaling notes -> Used in (links to examples).

---

## 6. Strategy selector (summary page)

A single page, `strategy/index.md`, with one matrix per decision axis and a short
questionnaire at the top ("Does the DUT have a clock? More than one? A bus? Async
inputs? Is there a register map? Is it reused at a higher level?"), each answer
pointing to a row.

Draft content:

### 6.1 Testbench architecture

| Level | Typical DUT | Architecture | Sequencing | Reuse expectation |
|---|---|---|---|---|
| Gate / cell | and_gate | 1 agent, env, test | Plain sequences | Promote agent to VIP only if reused |
| Block | counter, FSM | 1 agent + clk_rst agent | Base seq with knobs | Agent reusable, env not |
| Block, multi-port | FIFO, synchronizer | Multiple agents | Virtual sequence (no sequencer) | Agents reusable |
| IP | capstone | Multi-agent + RAL + virtual sequencer | Virtual + reg sequences | Env reused as sub-env |
| Subsystem | IP + fabric | Env of envs, block agents passive | Top virtual seqs calling sub-env seqs | Sub-envs reused unchanged |
| SoC | full chip | SoC env, VIPs at the pins, SW-driven tests | SW + UVM co-sequencing | Block checkers reused passively |

### 6.2 Stimulus strategy

| Level | Primary | Secondary | Do not |
|---|---|---|---|
| Gate | Exhaustive directed | Random for overlap/timing | Over-engineer constraints |
| Block | Constrained random with knobs | Directed corners (N-1, N, N+1) | Random without coverage |
| IP | Layered: reg seqs + traffic seqs via virtual seqs | Error injection callbacks | Monolithic test-specific sequences |
| SoC | Use-case scenarios, SW-driven | Random background traffic | Re-verify block corners |

### 6.3 Checker strategy

| Level | Logic checks | Timing checks | Where they live |
|---|---|---|---|
| Gate | Predictor + obligation scoreboard | Budget, skew, edges (GLS) | Separate scoreboard and timing checker |
| Block | Cycle-accurate predictor, SVA | Latency windows, setup/hold | Env + interface SVA |
| IP | Per-path scoreboards, RAL mirror | Protocol timing, IRQ latency | Env; protocol SVA in VIP |
| SoC | End-to-end data integrity, performance | System latency budgets | Reused block checkers (passive) + SoC checkers |

### 6.4 Housekeeping strategy

| Level | Config | Regression | Logging | Coverage |
|---|---|---|---|---|
| Gate | One cfg object | Makefile targets | Default verbosity | One covergroup |
| Block | Agent cfg + timing cfg override | YAML list, seeds | Report IDs per component | Covergroups + SVA cover |
| IP | Env cfg tree, plusargs | Nightly with seeds, mutant runs | Severity overrides, catchers | vplan traceability, merge |
| SoC | Hierarchical cfg, factory overrides per test | Tiered (smoke / nightly / weekly), partitioned compile | Log filtering, triage scripts | Merged coverage, waivers |

### 6.5 Scenario coverage matrix

A generated table (rows: every recipe; columns: every example) that marks where each
scenario is demonstrated. It is the check that the cookbook is "exhaustive": a recipe
with no example is a gap.

---

## 7. Roadmap

| Phase | Content | Exit criteria |
|---|---|---|
| **0. Foundation** | Repo, MkDocs site, `flow/Makefile.common`, snippet markers, page templates, CI that builds the site | Site builds; one placeholder page includes a snippet from a compiled file |
| **1. and_gate complete** | Finish placeholders (timing checker, value checker, coverage, timing seq, top, GLS run) in the skill repo; publish as chapter 00 | RTL and mutant runs pass the spec section 9 criteria on xrun; page has all 10 sections |
| **2. Single-agent block benches** | 01 ALU, 02 flop, 03 counter, 04 FSM; recipes B (constraints), C (SVA, predictors), D (clocking, setup/hold) | Each example: regression green, every checker has a killing mutant |
| **3. Multi-agent and CDC** | 05 FIFOs, 06a synchronizer, 06b deglitcher; clk_rst VIP promoted | Same + CDC timing recipes |
| **4. Protocol and registers** | 06c serial VIP, 06d register map with RAL; VIPs promoted to `lib/vip/` | VIP smoke tests standalone; RAL built-in seqs pass |
| **5. Capstone IP** | 07 with all components, virtual sequences, coverage closure | Coverage goals met; mutant kill rate reported |
| **6. Subsystem and SoC** | 08, 09; housekeeping and scaling recipes | Vertical reuse shown with zero edits to block envs |
| **7. Strategy selector** | Summary page, questionnaire, generated scenario matrix | Every recipe links to at least one example |

The strategy page is drafted in phase 0 (structure only) and filled as phases land.

---

## 8. Quality rules for every page

- Code on the site comes only from files that compiled and ran in CI. Anything not run
  is marked **UNTESTED**.
- Every checker has a mutant that it catches; the site shows the error message.
- Every pass criterion is a count, not just "0 errors".
- No vendor-specific constructs in examples unless shown in a vendor tab.
- Each page states the UVM and simulator version it was run with.

---

## 9. Decisions

Agreed on 2026-11-21. The full list, with later refinements, is in `ROADMAP.md` (D-01 to D-07).

1. Independent project: all examples live in this repository.
2. UVM IEEE 1800.2 by default, with a switch for legacy UVM 1.2.
3. Simulators: Xcelium (`xrun`) and open-source tools only.
4. Public repository and site.
5. The capstone is a whole independent example.
6. APB for registers, AXI-lite for subsystem and SoC (to be refined).
7. SoC uses a small open RISC-V core (candidate: PicoRV32) running C tests.
