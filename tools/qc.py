#!/usr/bin/env python3
"""Tool feedback for the cookbook: runs every QC check and prints one line per check.

Result per check: PASS, FAIL, or SKIP (with a reason). Overall is FAIL if any check
fails; with --strict, a SKIP also counts as a failure. Standard library only; external
tools are found on PATH or in .venv/bin and tools/bin.

Checks added in later steps (see ROADMAP.md): sim (P0.3), mutants (P0.4).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRA_PATH = [ROOT / ".venv" / "bin", ROOT / "tools" / "bin"]
EXCLUDE = {".git", ".venv", "site", ".qc", "tools/bin", "build", "results", "sandbox"}


def which(tool):
    path = os.pathsep.join([str(p) for p in EXTRA_PATH] + [os.environ.get("PATH", "")])
    return shutil.which(tool, path=path)


def files(*globs):
    out = []
    for g in globs:
        for p in ROOT.rglob(g):
            rel = p.relative_to(ROOT).as_posix()
            if not any(rel == e or rel.startswith(e + "/") for e in EXCLUDE):
                out.append(p)
    return sorted(set(out))


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def first_lines(text, n=3):
    lines = [l for l in text.splitlines() if l.strip()]
    s = " / ".join(lines[:n])
    return (s[:300] + "...") if len(s) > 300 else s


# ---------------------------------------------------------------- checks
def chk_steps():
    bad = []
    for p in files("steps/P*.md"):
        t = p.read_text()
        m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
        if not m:
            bad.append(f"{p.name}: no front matter")
            continue
        meta = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        if meta.get("id") != p.stem:
            bad.append(f"{p.name}: id mismatch")
        if meta.get("state") not in {"plan", "discuss", "refine", "implement", "feedback", "pass", "fail"}:
            bad.append(f"{p.name}: bad state")
    n = len(files("steps/P*.md"))
    return ("FAIL", "; ".join(bad)) if bad else ("PASS", f"{n} step file(s) valid")


def chk_decisions():
    sections = ["Context", "Criteria", "Options", "Evidence", "Scoring",
                "Recommendation", "Decision", "Revisit if"]
    states = {"proposed", "criteria-agreed", "evaluated", "accepted", "superseded"}
    drs = [p for p in files("decisions/DR-*.md")]
    if not drs:
        return "SKIP", "no decision records yet"
    bad = []
    for p in drs:
        t = p.read_text()
        m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
        meta = {k.strip(): v.strip() for k, v in
                (l.split(":", 1) for l in (m.group(1).splitlines() if m else []) if ":" in l)}
        if not re.match(r"^DR-\d{3}$", meta.get("id", "")) or not p.name.startswith(meta.get("id", "?") + "-"):
            bad.append(f"{p.name}: id")
        if meta.get("status") not in states:
            bad.append(f"{p.name}: status")
        missing = [s for s in sections if not re.search(rf"^## {re.escape(s)}\s*$", t, re.M)]
        if missing:
            bad.append(f"{p.name}: missing {', '.join(missing)}")
        if meta.get("status") == "accepted" and re.search(r"^## Decision\s*\n\s*\n_Owner", t, re.M):
            bad.append(f"{p.name}: accepted but Decision empty")
    return ("FAIL", "; ".join(bad[:5])) if bad else ("PASS", f"{len(drs)} record(s)")


def chk_headers():
    """SystemVerilog file header: File Name matches, Description and Revision History present."""
    svs = files("*.sv", "*.svh")
    if not svs:
        return "SKIP", "no SystemVerilog files yet"
    bad = []
    for p in svs:
        head = p.read_text(errors="replace")
        m = re.search(r"File Name\s*:\s*(\S+)", head[:2000])
        if not m or m.group(1) != p.name:
            bad.append(f"{p.relative_to(ROOT)}: File Name")
        if "Description" not in head[:3000]:
            bad.append(f"{p.relative_to(ROOT)}: Description")
        if "Revision History" not in head:
            bad.append(f"{p.relative_to(ROOT)}: Revision History")
    return ("FAIL", "; ".join(bad[:5])) if bad else ("PASS", f"{len(svs)} file(s)")


def chk_lint_rtl():
    rtl = [p for p in files("*.sv", "*.v") if "/design/rtl/" in p.as_posix() or "/dv/mutants/" in p.as_posix()]
    if not rtl:
        return "SKIP", "no RTL yet"
    v = which("verilator")
    if not v:
        return "SKIP", "verilator not installed"
    bad = []
    for p in rtl:
        rc, out = run([v, "--lint-only", "-Wall", "--timing", str(p)])
        if rc:
            bad.append(f"{p.relative_to(ROOT)}: {first_lines(out, 1)}")
    return ("FAIL", "; ".join(bad[:3])) if bad else ("PASS", f"{len(rtl)} file(s)")


def chk_lint_sv():
    svs = files("*.sv", "*.svh")
    if not svs:
        return "SKIP", "no SystemVerilog files yet"
    v = which("verible-verilog-lint")
    if not v:
        return "SKIP", "verible not installed (run tools/setup.sh)"
    rules = ROOT / ".rules.verible_lint"
    cmd = [v] + ([f"--rules_config={rules}"] if rules.exists() else []) + [str(p) for p in svs]
    rc, out = run(cmd)
    return ("FAIL", first_lines(out)) if rc else ("PASS", f"{len(svs)} file(s)")


def chk_docs():
    if not (ROOT / "mkdocs.yml").exists():
        return "SKIP", "no mkdocs.yml yet (P0.2)"
    m = which("mkdocs")
    if not m:
        return "SKIP", "mkdocs not installed (run tools/setup.sh)"
    rc, out = run([m, "build", "--strict", "--site-dir", str(ROOT / ".qc" / "site")])
    return ("FAIL", first_lines(out)) if rc else ("PASS", "strict build")


def chk_spell():
    c = which("codespell")
    if not c:
        return "SKIP", "codespell not installed (run tools/setup.sh)"
    targets = [str(p) for p in files("*.md", "*.sv", "*.svh", "*.py", "*.yml", "*.yaml")]
    if not targets:
        return "SKIP", "nothing to check"
    rc, out = run([c] + targets)
    return ("FAIL", first_lines(out)) if rc else ("PASS", f"{len(targets)} file(s)")


def chk_yaml():
    ys = files("*.yml", "*.yaml")
    if not ys:
        return "SKIP", "no YAML files yet"
    y = which("yamllint")
    if not y:
        return "SKIP", "yamllint not installed (run tools/setup.sh)"
    rc, out = run([y, "-s"] + [str(p) for p in ys])
    return ("FAIL", first_lines(out)) if rc else ("PASS", f"{len(ys)} file(s)")


def chk_python():
    py = files("*.py")
    rc, out = run([sys.executable, "-m", "py_compile"] + [str(p) for p in py])
    return ("FAIL", first_lines(out)) if rc else ("PASS", f"{len(py)} file(s) compile")


def chk_private():
    """Public repo: no machine paths, license files, or e-mail addresses in tracked text."""
    pat = re.compile(r"(/home/[a-z]|/mnt/|license\.dat|CDS_LIC_FILE\s*=|[\w.+-]+@(?!anthropic\.com)[\w-]+\.[a-z]{2,})")  # qc-private: allow
    hits = []
    for p in files("*.md", "*.sv", "*.svh", "*.py", "*.yml", "*.yaml", "*.sh", "Makefile*", "*.f", "*.tcl"):
        for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if pat.search(line) and "qc-private: allow" not in line:
                hits.append(f"{p.relative_to(ROOT)}:{i}")
    return ("FAIL", "; ".join(hits[:5])) if hits else ("PASS", "no private data patterns")


FAST = [("steps", chk_steps), ("decisions", chk_decisions), ("private", chk_private), ("headers", chk_headers),
        ("python", chk_python), ("spell", chk_spell), ("yaml", chk_yaml)]
FULL = FAST + [("lint-rtl", chk_lint_rtl), ("lint-sv", chk_lint_sv), ("docs", chk_docs)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fast", action="store_true", help="quick checks only (pre-commit)")
    ap.add_argument("--strict", action="store_true", help="treat SKIP as failure")
    ap.add_argument("--json", help="write results to this file")
    a = ap.parse_args()

    results = []
    for name, fn in (FAST if a.fast else FULL):
        status, detail = fn()
        results.append({"name": name, "status": status, "detail": detail})
        print(f"QC {name:<9} {status:<5} {detail}")
    failed = any(r["status"] == "FAIL" or (a.strict and r["status"] == "SKIP") for r in results)
    overall = "FAIL" if failed else "PASS"
    print(f"QC overall   {overall}")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"overall": overall, "checks": results}, indent=2))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
