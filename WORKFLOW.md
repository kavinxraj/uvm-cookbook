# Workflow

Every piece of work in this repository is a **step** with an ID (for example `P1.3`) from
`ROADMAP.md`. Each step moves through one loop, and each step ends in exactly one commit.

```
PLAN ─► DISCUSS ─► REFINE ─► IMPLEMENT ─► FEEDBACK (tool + human) ─┬─► PASS ─► COMMIT ─► next step
           ▲                                                       │
           └──────────────────────────── FAIL ◄────────────────────┘
```

## 1. Stages

| Stage | Who | What happens | Exit condition | Recorded in |
|---|---|---|---|---|
| **PLAN** | AI drafts, human reads | Goal, scope, deliverables, QC gates, and done criteria for the step, copied from `ROADMAP.md` and made concrete | Step file exists with a Plan section | `steps/<ID>.md` § Plan |
| **DISCUSS** | Both | Open questions, options with a recommendation, risks | Every open question has an answer | § Discussion |
| **REFINE** | AI writes, human confirms | The plan is updated with the answers; final file list and acceptance checks | Human says "go" | § Refined plan |
| **IMPLEMENT** | AI (or human) | Write the files listed in the refined plan, and nothing else | All listed files written | § Implementation |
| **FEEDBACK: tool** | Tools | `python3 tools/step.py qc <ID>` runs `tools/qc.py` (lint, docs, spelling, headers, simulation, mutants) and appends the results as a new round | Round recorded | § Feedback, round N |
| **FEEDBACK: human** | Human | Review against the checklist in the step file; write comments; give a verdict | Verdict given | § Feedback, round N |
| **PASS** | Human | `step.py review <ID> --verdict pass` (allowed only if the tool round passed) | State is `pass` | Log |
| **FAIL** | Human | `step.py review <ID> --verdict fail --notes "..."`; the loop returns to DISCUSS with the notes as the first topic | State is `fail` -> `discuss` | Log |
| **COMMIT** | AI proposes the message, human approves | One commit with the trailer `Step: <ID>`; the `commit-msg` hook refuses it unless the step state is `pass` | Commit exists | git history |
| **NEXT STEP** | AI | `step.py status` shows the next step; it starts at PLAN | — | — |

## 2. Rules

1. **No implementation before the human says "go"** at the end of REFINE.
2. **Only the human gives the human verdict.** The AI never runs `step.py review` unless
   the human has stated the verdict in their own words, and then records it as given.
3. **A tool FAIL blocks PASS.** The human may override only with a written reason
   (`--override "reason"`), and the reason is kept in the step file.
4. **A SKIP is not a PASS.** If a check is skipped (for example, a tool is not installed),
   the round shows it, and the human decides whether that is acceptable for this step.
5. **One step, one commit.** The step file is part of the commit, so the history keeps the
   plan, the discussion, every feedback round, and the verdict next to the code.
6. **Never bypass the hooks** (`--no-verify`). If a hook is wrong, fix the hook in its own step.
7. **Report outcomes faithfully.** A failing run is reported with its output. Anything not
   run on a simulator is marked `UNTESTED`.
8. **Scope is fixed at REFINE.** New ideas found during IMPLEMENT go into the step file's
   "Follow-ups" list, not into the current commit.

## 3. Commands

```bash
python3 tools/step.py status                 # all steps, state, and last commit
python3 tools/step.py new P1.3 "and_gate agent"
python3 tools/step.py move P1.3 discuss      # advance one stage (transitions are checked)
python3 tools/step.py qc P1.3                # tool feedback round (runs tools/qc.py)
python3 tools/step.py review P1.3 --verdict pass --by "<reviewer>" --notes "..."
python3 tools/qc.py                          # run QC alone (no step file change)
python3 tools/qc.py --fast                   # quick checks only (used by the pre-commit hook)
```

## 4. Allowed state transitions

| From | To |
|---|---|
| plan | discuss |
| discuss | refine |
| refine | implement, discuss |
| implement | feedback |
| feedback | pass, fail (via `review` only) |
| fail | discuss |
| pass | (commit; then the step is shown as committed) |

## 5. Human review checklist (default)

Each step file carries this list; steps add their own items.

- [ ] Does the result match the refined plan, and nothing more?
- [ ] Is it correct? (Read the code or page, not only the QC summary.)
- [ ] Is it clear to a reader who starts at this page?
- [ ] Is every checker proven by a mutant (if the step adds checkers)?
- [ ] Are the follow-ups recorded?
