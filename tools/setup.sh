#!/usr/bin/env bash
# One-time setup: Python QC tools in .venv, Verible in tools/bin, git hooks.
# Re-running is safe.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r tools/requirements.txt
echo "python tools: $(.venv/bin/mkdocs --version | head -1)"

if [ ! -x tools/bin/verible-verilog-lint ]; then
  mkdir -p tools/bin
  url=$(curl -fsSL https://api.github.com/repos/chipsalliance/verible/releases/latest \
        | grep -o '"browser_download_url": *"[^"]*linux-static-x86_64.tar.gz"' \
        | head -1 | sed 's/.*"\(https[^"]*\)"/\1/')
  if [ -n "${url:-}" ]; then
    tmp=$(mktemp -d)
    curl -fsSL "$url" -o "$tmp/verible.tgz"
    tar -xzf "$tmp/verible.tgz" -C "$tmp"
    find "$tmp" -type f -name 'verible-verilog-*' -exec cp {} tools/bin/ \;
    rm -rf "$tmp"
    echo "verible: $(tools/bin/verible-verilog-lint --version | head -1)"
  else
    echo "verible: download URL not found; install it by hand into tools/bin" >&2
  fi
fi

git config core.hooksPath .githooks
echo "git hooks: .githooks"
