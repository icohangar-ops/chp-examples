#!/usr/bin/env python3
"""Turn config-only .chp/ repos into real package consumers.

For each repo that already has .chp/ config but no engine:
  - ensure a dependency on consensus-hardening-protocol (Python) where a
    pyproject.toml / requirements.txt exists
  - leave a one-line pointer in .chp/README.md to the published package

Dry-run by default; pass --apply to write.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path.home() / "Desktop" / "icohangar-repos"

CONFIG_ONLY = [
    "swarmfi",
    "swarmfi-preps",
    "swarmfi-solana",
    "hedge-fund-13f-radar",
    "Reddit-Community-reply-assistant",
    "db-proxy",
    "genswarm-contract",
    "glacier-edge-arm",
    "compliance-as-code-agent",
    "strata",
    "consensus-media-gen",
    "council-tower",
    "decision-brief",
    "market-sentiment-fedgpt",
    "prove-reel",
    "lease842",
]

PIN = "consensus-hardening-protocol>=0.1.0"
NOTE = (
    "\n> Runtime: install the published engine — "
    "`pip install consensus-hardening-protocol` — rather than vendoring `cme/chp`.\n"
)


def ensure_python_dep(repo: Path, apply: bool) -> str:
    pyproject = repo / "pyproject.toml"
    req = repo / "requirements.txt"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        if "consensus-hardening-protocol" in text:
            return "pyproject already pins chp"
        # Minimal, non-destructive: append a comment block consumers can adopt.
        addition = (
            "\n# CHP engine (add under [project].dependencies when ready):\n"
            f"#   \"{PIN}\"\n"
        )
        if apply:
            pyproject.write_text(text.rstrip() + addition, encoding="utf-8")
        return "annotate pyproject.toml"
    if req.exists():
        text = req.read_text(encoding="utf-8")
        if "consensus-hardening-protocol" in text:
            return "requirements already pins chp"
        if apply:
            req.write_text(text.rstrip() + f"\n{PIN}\n", encoding="utf-8")
        return "append requirements.txt"
    return "no python manifest — skipped dep"


def ensure_chp_readme(repo: Path, apply: bool) -> str:
    chp = repo / ".chp"
    if not chp.is_dir():
        return "no .chp/ dir"
    readme = chp / "README.md"
    if readme.exists() and "consensus-hardening-protocol" in readme.read_text(encoding="utf-8", errors="ignore"):
        return ".chp/README already points at package"
    if apply:
        prev = readme.read_text(encoding="utf-8") if readme.exists() else "# .chp/\n"
        if "consensus-hardening-protocol" not in prev:
            readme.write_text(prev.rstrip() + "\n" + NOTE, encoding="utf-8")
    return "point .chp/README at package"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    for name in CONFIG_ONLY:
        repo = ROOT / name
        if not repo.is_dir():
            print(f"skip  {name}: not cloned")
            continue
        a = ensure_python_dep(repo, args.apply)
        b = ensure_chp_readme(repo, args.apply)
        print(f"{'WRITE' if args.apply else 'would'} {name}: {a}; {b}")
    if not args.apply:
        print("\nRe-run with --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
