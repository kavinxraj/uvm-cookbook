# UVM Cookbook: instructions for AI assistants

Read this file, then `WORKFLOW.md`, then run `python3 tools/step.py status` and read the
step file of the active step before doing anything.

## What this project is

A public, example-driven UVM cookbook site: from a 2-input gate to a RISC-V SoC bench.
Vision: `PLAN.md`. Step-by-step plan and decisions: `ROADMAP.md`.

## Rules

1. **Follow the loop in `WORKFLOW.md`.** PLAN -> DISCUSS -> REFINE -> IMPLEMENT ->
   FEEDBACK (tool + human) -> PASS -> COMMIT, or FAIL -> DISCUSS. One step, one commit.
2. **Do not implement before the human says "go"** at the end of REFINE. In DISCUSS,
   state the most likely reading, list options with a recommendation, and wait.
3. **Never give the human verdict yourself.** Run `step.py review` only to record a
   verdict the human stated in their own words, with `--by` set to what they said.
4. **Never bypass hooks** (`--no-verify`) and never commit without a passed step.
   Propose the commit message and wait for approval.
5. **Report outcomes faithfully.** Show failing output. Mark anything not run on a
   simulator as `UNTESTED`. A passing xrun run is judged from the UVM report summary and
   the pass-criteria line, not from the exit code.
6. **Public repository.** No machine paths, license paths, or personal data in committed
   files. Local simulator settings go in `flow/env.local.sh` (git-ignored).
   `tools/qc.py` checks this (`private`).
7. **Code on the site comes from real files** through snippet markers; never paste code
   into pages by hand.
8. **Every checker needs a mutant** that it catches before its step can pass.
9. **Scope is fixed at REFINE.** New ideas go to the step's Follow-ups list.

## Conventions

- SystemVerilog file header: File Name, Author, Created On, Project, Standard,
  Description, and a Revision History footer (checked by `qc.py headers`).
- Ports: `i_<name>` inputs, `o_<name>` outputs.
- UVM: IEEE 1800.2 default (`UVM=ieee`), legacy switch `UVM=1.2`.
- Simulators: `xrun` and open-source tools only.
