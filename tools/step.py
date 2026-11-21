#!/usr/bin/env python3
"""Step tracker for the PLAN -> DISCUSS -> REFINE -> IMPLEMENT -> FEEDBACK loop.

Each step is a Markdown file steps/<ID>.md with a small front matter block:

    ---
    id: P1.3
    title: and_gate agent
    state: plan
    ---

See WORKFLOW.md for the stages and rules. Standard library only.
"""

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = ROOT / "steps"
TEMPLATE = STEPS / "_template.md"

STATES = ["plan", "discuss", "refine", "implement", "feedback", "pass", "fail"]
MOVES = {  # transitions allowed with `move`; pass/fail only via `review`
    "plan": ["discuss"],
    "discuss": ["refine"],
    "refine": ["implement", "discuss"],
    "implement": ["feedback"],
    "feedback": [],
    "fail": ["discuss"],
    "pass": [],
}
ID_RE = re.compile(r"^P\d+\.\d+$")


def now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def step_path(sid):
    return STEPS / f"{sid}.md"


def read_step(sid, text=None):
    if text is None:
        p = step_path(sid)
        if not p.exists():
            sys.exit(f"step {sid}: no file {p.relative_to(ROOT)}")
        text = p.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit(f"step {sid}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text


def write_state(sid, text, new_state, note):
    text = re.sub(r"^state: .*$", f"state: {new_state}", text, count=1, flags=re.M)
    text = text.rstrip("\n") + f"\n| {now()} | {new_state} | {note} |\n"
    step_path(sid).write_text(text)


def cmd_new(a):
    if not ID_RE.match(a.id):
        sys.exit("ID must look like P1.3")
    p = step_path(a.id)
    if p.exists():
        sys.exit(f"{p.relative_to(ROOT)} already exists")
    text = TEMPLATE.read_text().replace("{{ID}}", a.id).replace("{{TITLE}}", a.title)
    text = text.rstrip("\n") + f"\n| {now()} | plan | step created |\n"
    p.write_text(text)
    print(f"created {p.relative_to(ROOT)} (state: plan)")


def cmd_move(a):
    meta, text = read_step(a.id)
    cur = meta.get("state")
    if a.to not in MOVES.get(cur, []):
        allowed = ", ".join(MOVES.get(cur, [])) or "none (use `review` from feedback)"
        sys.exit(f"step {a.id}: cannot move {cur} -> {a.to}. Allowed: {allowed}")
    write_state(a.id, text, a.to, a.note or "")
    print(f"{a.id}: {cur} -> {a.to}")


def cmd_qc(a):
    meta, text = read_step(a.id)
    if meta.get("state") != "feedback":
        sys.exit(f"step {a.id}: state is {meta.get('state')}; move it to feedback first")
    out = ROOT / ".qc" / "last.json"
    args = [sys.executable, str(ROOT / "tools" / "qc.py"), "--json", str(out)]
    if a.strict:
        args.append("--strict")
    rc = subprocess.call(args, cwd=ROOT)
    res = json.loads(out.read_text())
    n = len(re.findall(r"^### Round \d+", text, re.M)) + 1
    rows = "\n".join(f"| {r['name']} | {r['status']} | {r['detail']} |" for r in res["checks"])
    block = (
        f"### Round {n} ({now()})\n\n"
        f"**Tool feedback: {res['overall']}**\n\n"
        f"| Check | Result | Detail |\n|---|---|---|\n{rows}\n\n"
        f"**Human feedback:** _(reviewer writes here)_\n\n"
    )
    marker = "<!-- feedback rounds go above this line -->"
    if marker not in text:
        sys.exit(f"step {a.id}: feedback marker missing in the step file")
    text = text.replace(marker, block + marker, 1)
    text = re.sub(r"^last_qc: .*$", f"last_qc: {res['overall']}", text, count=1, flags=re.M)
    text = text.rstrip("\n") + f"\n| {now()} | feedback | tool round {n}: {res['overall']} |\n"
    step_path(a.id).write_text(text)
    print(f"{a.id}: tool round {n} recorded ({res['overall']})")
    return rc


def cmd_review(a):
    meta, text = read_step(a.id)
    if meta.get("state") != "feedback":
        sys.exit(f"step {a.id}: state is {meta.get('state')}; review happens in feedback")
    if not a.by:
        sys.exit("--by <reviewer> is required")
    last = meta.get("last_qc", "none")
    if a.verdict == "pass" and last != "PASS":
        if not a.override:
            sys.exit(f"step {a.id}: last tool round is {last}; pass needs --override \"reason\"")
    note = f"human verdict {a.verdict.upper()} by {a.by}"
    if a.override:
        note += f" (override: {a.override})"
    if a.notes:
        note += f": {a.notes}"
    write_state(a.id, text, a.verdict, note.replace("|", "/"))
    if a.verdict == "fail":
        _, text = read_step(a.id)
        write_state(a.id, text, "discuss", "back to DISCUSS with the review notes")
        print(f"{a.id}: FAIL recorded; state is discuss")
    else:
        print(f"{a.id}: PASS recorded; ready to commit with trailer 'Step: {a.id}'")


def committed(sid):
    try:
        out = subprocess.check_output(
            ["git", "log", "--format=%h", f"--grep=^Step: {re.escape(sid)}$"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        return out.split()[0] if out.split() else ""
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def cmd_status(a):
    files = sorted(STEPS.glob("P*.md"),
                   key=lambda p: [int(x) for x in p.stem[1:].split(".")])
    print(f"{'ID':<7} {'STATE':<10} {'QC':<6} {'COMMIT':<9} TITLE")
    for p in files:
        meta, _ = read_step(p.stem)
        print(f"{meta['id']:<7} {meta.get('state', '?'):<10} {meta.get('last_qc', '-'):<6} "
              f"{committed(meta['id']) or '-':<9} {meta.get('title', '')}")
    if not files:
        print("(no steps yet)")


def cmd_check_commit(a):
    """Called by the commit-msg hook with the message file."""
    msg = Path(a.msgfile).read_text()
    m = re.search(r"^Step: (P\d+\.\d+)\s*$", msg, re.M)
    if not m:
        sys.exit("commit refused: message needs a trailer line 'Step: <ID>' (see WORKFLOW.md)")
    sid = m.group(1)
    try:
        staged = subprocess.check_output(["git", "show", f":steps/{sid}.md"], cwd=ROOT, text=True,
                                         stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        sys.exit(f"commit refused: steps/{sid}.md is not staged")
    meta, _ = read_step(sid, staged)
    if meta.get("state") != "pass":
        sys.exit(f"commit refused: step {sid} state is {meta.get('state')}, needs pass")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("id"); s.add_argument("title")
    s.set_defaults(fn=cmd_new)
    s = sub.add_parser("move"); s.add_argument("id"); s.add_argument("to", choices=STATES)
    s.add_argument("--note"); s.set_defaults(fn=cmd_move)
    s = sub.add_parser("qc"); s.add_argument("id"); s.add_argument("--strict", action="store_true")
    s.set_defaults(fn=cmd_qc)
    s = sub.add_parser("review"); s.add_argument("id")
    s.add_argument("--verdict", required=True, choices=["pass", "fail"])
    s.add_argument("--by"); s.add_argument("--notes"); s.add_argument("--override")
    s.set_defaults(fn=cmd_review)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("check-commit"); s.add_argument("msgfile"); s.set_defaults(fn=cmd_check_commit)
    a = ap.parse_args()
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
