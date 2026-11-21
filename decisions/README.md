# Decision records

A decision record (DR) is written for any choice that is hard to reverse or affects more
than one step. Small choices stay in the step file's Discussion table. The process is in
`WORKFLOW.md` section 6.

Create one with:

```bash
python3 tools/step.py decision new P0.2 "Documentation site generator"
python3 tools/step.py decision list
```

Status values: `proposed`, `criteria-agreed`, `evaluated`, `accepted`, `superseded`.
