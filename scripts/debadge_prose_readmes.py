#!/usr/bin/env python3
"""Sweep CHP prose claims out of READMEs that have no implementation.

Operates on local clones under ~/Desktop/icohangar-repos. Dry-run by default.
Pass --apply to write.

Targets the 22 prose-only repos from the consolidation map. Removes or rewrites
lines that claim CHP / Consensus Hardening Protocol without a corresponding
implementation in the repo.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path.home() / "Desktop" / "icohangar-repos"

PROSE_ONLY = [
    "poc-revenue",
    "sbc-ledger",
    "combination-accounting",
    "nexus-monitor",
    "cuec-review",
    "aegis-protocol",
    "pythia",
    "two-key",
    "countersign",
    "injection-arena",
    "qwen-agent-runtime",
    "deltafin",
    "agentforge",
    "operational-intelligence",
    "swarmfi-executor",
    "p2p-copilot",
    "portfolio-agent-platform",
    "policyforge",
    "cubiczan-mcp-server",
    "software-factory",
    "earnings-call-nlp-lab",
    "Cubiczan",
]

# Lines that are pure badge/claim, safe to drop entirely.
DROP = re.compile(
    r"(?i)(consensus.?hardening|^\s*.*\bCHP\b.*$|hardened by CHP|CHP-governed|CHP-aligned)",
)


def rewrite(text: str) -> tuple[str, int]:
    out: list[str] = []
    dropped = 0
    for line in text.splitlines(keepends=True):
        # Drop standalone claim bullets / one-liners; keep code fences untouched.
        stripped = line.strip()
        if stripped.startswith("```"):
            out.append(line)
            continue
        if DROP.search(stripped) and len(stripped) < 200:
            # Soften rather than delete if the line has other substance.
            if re.search(r"(?i)\b(CHP|consensus hardening)\b", stripped) and (
                "http" in stripped or "install" in stripped.lower()
            ):
                out.append(line)
                continue
            if re.fullmatch(r"[-*+]\s+.*", stripped) or "CHP" in stripped or "consensus" in stripped.lower():
                dropped += 1
                continue
        out.append(line)
    return "".join(out), dropped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    total = 0
    for name in PROSE_ONLY:
        repo = ROOT / name
        readme = next((p for p in repo.glob("README*") if p.is_file()), None) if repo.is_dir() else None
        if not readme:
            print(f"skip  {name}: no local README")
            continue
        new, n = rewrite(readme.read_text(encoding="utf-8", errors="ignore"))
        if n == 0:
            print(f"ok    {name}: no claim lines matched")
            continue
        total += n
        print(f"{'WRITE' if args.apply else 'would'} {name}: drop {n} line(s) in {readme.name}")
        if args.apply:
            readme.write_text(new, encoding="utf-8")
    print(f"\n{'applied' if args.apply else 'dry-run'}: {total} lines across prose-only READMEs")
    if not args.apply:
        print("Re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
