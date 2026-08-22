"""control-spine — ICFR evidence pack, R0 + human lock via published CHP.

Retargeted from control-spine, which reimplemented R0 and hashing locally.
This example delegates the R0 gate to `chp.evaluate_r0_gate` and seals a pack
with a content hash compatible with CHP canonical JSON (sorted keys, no spaces).
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from chp import evaluate_r0_gate


def content_hash(payload: Any) -> str:
    """SHA-256 over CHP-shaped canonical JSON (spec §3.1 subset)."""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(body.encode("utf-8")).hexdigest()


def seal_icfr_pack(
    *,
    control_id: str,
    population_count: int,
    threshold: str,
    engine_id: str,
    owner_signoff: str,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    inputs = {
        "control_id": control_id,
        "population_count": population_count,
        "threshold": threshold,
    }
    inputs_hash = content_hash(inputs)

    r0 = evaluate_r0_gate(
        solvable=population_count > 0,
        scoped=bool(control_id and threshold),
        valid=bool(engine_id and inputs_hash),
        worth_it=control_id.startswith("ICFR-"),
    )
    # Human gate: owner must differ from the engine that prepared the pack.
    human_ok = bool(owner_signoff) and owner_signoff.strip() != engine_id.strip()
    blocking = [f for f in findings if f.get("blocking")]

    if r0.verdict.value != "PASS" or not human_ok or blocking:
        lock_state = "HALT" if (r0.verdict.value != "PASS" or not human_ok) else "EXPLORING"
    else:
        lock_state = "LOCKED"

    pack = {
        "control_id": control_id,
        "engine_id": engine_id,
        "owner_signoff": owner_signoff,
        "inputs_hash": inputs_hash,
        "r0": {"results": r0.results, "verdict": r0.verdict.value},
        "human_gate": "PASS" if human_ok else "FATAL",
        "findings": findings,
        "lock_state": lock_state,
    }
    pack["spine_hash"] = content_hash(pack)
    return pack


def exit_code(pack: dict[str, Any]) -> int:
    return 0 if pack.get("lock_state") in {"LOCKED", "EXPLORING"} else 2


def main() -> None:
    sealed = seal_icfr_pack(
        control_id="ICFR-REV-01",
        population_count=1284,
        threshold="all invoices > $10k reviewed",
        engine_id="lease842",
        owner_signoff="controller@example.com",
        findings=[],
    )
    print(f"lock_state : {sealed['lock_state']}")
    print(f"r0         : {sealed['r0']}")
    print(f"spine_hash : {sealed['spine_hash'][:24]}…")
    print(f"exit_code  : {exit_code(sealed)}")

    halted = seal_icfr_pack(
        control_id="ICFR-REV-01",
        population_count=0,
        threshold="all invoices > $10k reviewed",
        engine_id="lease842",
        owner_signoff="lease842",  # same as engine — human gate fails
        findings=[{"code": "EMPTY", "message": "no population", "blocking": True}],
    )
    print(f"\nempty population lock_state: {halted['lock_state']} exit={exit_code(halted)}")


if __name__ == "__main__":
    main()
